import pandas as pd
import plotly.graph_objects as go

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import OuterRef, Subquery, Count
from django.http import JsonResponse
from django.utils import timezone
from django.utils.text import slugify

from .models import Category, Store, Component, PriceHistory, Watchlist
from .forms import RegisterForm, LoginForm, WatchlistForm, ComponentSearchForm, AddComponentForm

STORE_COLORS = {
    'Citilink':   '#e85d00',
    'DNS':        '#005ecb',
    'М.Видео':    '#00a650',
    'Эльдорадо':  '#f5a623',
}
STORE_FILLS = {
    'Citilink':  'rgba(232,93,0,.09)',
    'DNS':       'rgba(0,94,203,.09)',
    'М.Видео':   'rgba(0,166,80,.09)',
    'Эльдорадо': 'rgba(245,166,35,.09)',
}
ALL_STORES = list(STORE_COLORS.keys())


def _annotate_prices(qs):
    def _subq(store_name):
        return Subquery(
            PriceHistory.objects
            .filter(component=OuterRef('pk'), store__name=store_name)
            .order_by('-scraped_at').values('price')[:1]
        )
    return qs.annotate(
        citilink_price=_subq('Citilink'),
        dns_price=_subq('DNS'),
        mvideo_price=_subq('М.Видео'),
        eldorado_price=_subq('Эльдорадо'),
    )


def _best_deal(citilink, dns, mvideo, eldorado):
    prices = {'Citilink': citilink, 'DNS': dns, 'М.Видео': mvideo, 'Эльдорадо': eldorado}
    valid = {k: v for k, v in prices.items() if v}
    if not valid:
        return None, None
    best = min(valid, key=valid.get)
    return best, valid[best]


def index(request):
    categories = Category.objects.annotate(cnt=Count('components')).filter(cnt__gt=0)
    total_components = Component.objects.count()

    # Pandas: avg/min/max per category for analytics table
    cat_stats = []
    price_qs = PriceHistory.objects.select_related('component__category').values(
        'price', 'component__category__name', 'component__category__icon'
    )
    if price_qs.exists():
        df = pd.DataFrame(list(price_qs))
        stats = (
            df.groupby(['component__category__name', 'component__category__icon'])['price']
            .agg(avg='mean', min_p='min', max_p='max')
            .reset_index()
        )
        for _, row in stats.iterrows():
            cat_stats.append({
                'name': row['component__category__name'],
                'icon': row['component__category__icon'],
                'avg': int(row['avg']),
                'min_p': int(row['min_p']),
                'max_p': int(row['max_p']),
            })
        cat_stats.sort(key=lambda x: x['avg'], reverse=True)

    # Top 8 deals by biggest Citilink vs DNS spread
    components = _annotate_prices(Component.objects.select_related('category'))
    deals = []
    for c in components:
        if c.citilink_price and c.dns_price:
            savings = abs(c.citilink_price - c.dns_price)
            best = min(c.citilink_price, c.dns_price)
            deals.append({'component': c, 'savings': savings, 'best_price': best})
    deals.sort(key=lambda x: x['savings'], reverse=True)

    global_min_price = min((s['min_p'] for s in cat_stats), default=None)

    return render(request, 'monitor/index.html', {
        'categories': categories,
        'total_components': total_components,
        'cat_stats': cat_stats,
        'top_deals': deals[:8],
        'global_min_price': global_min_price,
    })


def catalog(request):
    cat_slug = request.GET.get('cat', '').strip()
    query = request.GET.get('q', '').strip()

    all_categories = Category.objects.annotate(cnt=Count('components')).filter(cnt__gt=0)
    active_category = None
    if cat_slug:
        active_category = get_object_or_404(Category, slug=cat_slug)

    qs = Component.objects.select_related('category')
    if active_category:
        qs = qs.filter(category=active_category)
    if query:
        qs = qs.filter(name__icontains=query)
    qs = _annotate_prices(qs).order_by('category', 'name')

    watchlist_ids = set()
    if request.user.is_authenticated:
        watchlist_ids = set(request.user.watchlist.values_list('component_id', flat=True))

    rows = []
    for c in qs:
        best_store, best_price = _best_deal(c.citilink_price, c.dns_price, c.mvideo_price, c.eldorado_price)
        rows.append({
            'component': c,
            'citilink': c.citilink_price,
            'dns': c.dns_price,
            'mvideo': c.mvideo_price,
            'eldorado': c.eldorado_price,
            'best_store': best_store,
            'best_price': best_price,
            'in_watchlist': c.id in watchlist_ids,
        })

    show_specs = active_category and active_category.name == 'Ноутбуки'

    return render(request, 'monitor/catalog.html', {
        'categories': all_categories,
        'active_category': active_category,
        'rows': rows,
        'query': query,
        'show_specs': show_specs,
        'search_form': ComponentSearchForm(initial={'q': query}),
    })


def component_detail(request, pk):
    component = get_object_or_404(Component.objects.select_related('category'), pk=pk)

    in_watchlist = False
    watchlist_entry = None
    if request.user.is_authenticated:
        watchlist_entry = Watchlist.objects.filter(
            user=request.user, component=component
        ).first()
        in_watchlist = watchlist_entry is not None

    # Build Plotly chart
    plotly_json = None
    records = PriceHistory.objects.filter(component=component).select_related('store').order_by('scraped_at')
    if records.exists():
        df = pd.DataFrame(list(records.values('store__name', 'price', 'scraped_at')))
        colors = STORE_COLORS
        fills = STORE_FILLS
        fig = go.Figure()
        for store in df['store__name'].unique():
            sub = df[df['store__name'] == store].sort_values('scraped_at')
            c = colors.get(store, '#888')
            fig.add_trace(go.Scatter(
                x=sub['scraped_at'].tolist(),
                y=sub['price'].tolist(),
                name=store,
                mode='lines+markers',
                line=dict(color=c, width=2.5),
                marker=dict(size=5, color=c, line=dict(width=1.5, color='white')),
                fill='tozeroy',
                fillcolor=fills.get(store, 'rgba(0,0,0,.05)'),
                hovertemplate='<b>%{y:,.0f} ₽</b>  %{x|%d.%m.%Y}<extra>' + store + '</extra>',
            ))
        fig.update_layout(
            xaxis_title=None, yaxis_title='Цена, ₽', yaxis_tickformat=',d',
            hovermode='x unified',
            legend=dict(orientation='h', y=1.05, x=0),
            plot_bgcolor='white', paper_bgcolor='white',
            margin=dict(t=20, b=30, l=10, r=10),
            font=dict(family='Inter, sans-serif', size=12, color='#555'),
        )
        fig.update_xaxes(showgrid=False, showline=True, linecolor='#f0f0f0')
        fig.update_yaxes(showgrid=True, gridcolor='#f5f5f5', zeroline=False)
        plotly_json = fig.to_json()

    all_prices = {s: component.get_latest_price(s) for s in ALL_STORES}

    similar = _annotate_prices(
        Component.objects.filter(category=component.category)
        .exclude(pk=component.pk).select_related('category')
    )[:6]

    return render(request, 'monitor/component_detail.html', {
        'component': component,
        'all_prices': all_prices,
        'store_colors': STORE_COLORS,
        'plotly_json': plotly_json,
        'in_watchlist': in_watchlist,
        'watchlist_form': WatchlistForm(instance=watchlist_entry) if request.user.is_authenticated else None,
        'watchlist_entry': watchlist_entry,
        'similar': similar,
    })


@login_required
def watchlist_view(request):
    items = Watchlist.objects.filter(user=request.user).select_related('component__category')
    enriched = []
    for item in items:
        prices = {s: item.component.get_latest_price(s) for s in ALL_STORES}
        valid = {k: v for k, v in prices.items() if v}
        best_store = min(valid, key=valid.get) if valid else None
        best_price = valid[best_store] if best_store else None
        enriched.append({
            'item': item,
            'prices': prices,
            'best_store': best_store,
            'best_price': best_price,
            'target_reached': bool(item.target_price and best_price and best_price <= item.target_price),
        })
    return render(request, 'monitor/watchlist.html', {
        'items': enriched,
        'stores': ALL_STORES,
        'store_colors': STORE_COLORS,
    })


def add_to_watchlist(request, component_id):
    component = get_object_or_404(Component, id=component_id)
    entry, _ = Watchlist.objects.get_or_create(user=request.user, component=component)
    if request.method == 'POST':
        form = WatchlistForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            messages.success(request, f'«{component.name}» добавлен в список отслеживания.')
    return redirect('component_detail', pk=component.pk)


@login_required
def remove_from_watchlist(request, component_id):
    Watchlist.objects.filter(user=request.user, component_id=component_id).delete()
    messages.info(request, 'Товар удалён из списка отслеживания.')
    return redirect('watchlist')



def add_component(request):
    if request.method == 'POST':
        form = AddComponentForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            base_slug = slugify(cd['name'], allow_unicode=True)[:380]
            slug, n = base_slug, 1
            while Component.objects.filter(slug=slug).exists():
                slug = f'{base_slug}-{n}'
                n += 1
            component = Component.objects.create(
                name=cd['name'], category=cd['category'],
                specs=cd.get('specs', ''), slug=slug,
            )
            now = timezone.now()
            store_map = {'price_citilink': 'Citilink', 'price_dns': 'DNS',
                         'price_mvideo': 'М.Видео', 'price_eldorado': 'Эльдорадо'}
            for field, store_name in store_map.items():
                price = cd.get(field)
                if price:
                    store, _ = Store.objects.get_or_create(name=store_name)
                    PriceHistory.objects.create(component=component, store=store,
                                                price=price, scraped_at=now)
            messages.success(request, f'«{component.name}» добавлен в каталог.')
            return redirect('component_detail', pk=component.pk)
    else:
        form = AddComponentForm()
    return render(request, 'monitor/add_component.html', {'form': form})

@login_required
def profile_view(request):
    from django.utils import timezone

    items = Watchlist.objects.filter(user=request.user).select_related('component__category').order_by('-added_at')

    enriched = []
    total_savings = 0
    target_reached_count = 0
    categories_seen = set()

    for item in items:
        prices = {s: item.component.get_latest_price(s) for s in ALL_STORES}
        valid = {k: v for k, v in prices.items() if v}
        best_store = min(valid, key=valid.get) if valid else None
        best_price = valid[best_store] if best_store else None
        worst_price = max(valid.values()) if valid else None
        savings = (worst_price - best_price) if (best_price and worst_price) else 0
        total_savings += savings
        target_ok = bool(item.target_price and best_price and best_price <= item.target_price)
        if target_ok:
            target_reached_count += 1
        categories_seen.add(item.component.category.name)
        enriched.append({
            'item': item,
            'prices': prices,
            'best_store': best_store,
            'best_price': best_price,
            'savings': savings,
            'target_ok': target_ok,
        })

    enriched.sort(key=lambda x: (-int(x['target_ok']), -(x['savings'] or 0)))

    days_joined = (timezone.now() - request.user.date_joined).days

    # Grouped bar chart — price per store for each watchlist item (max 12)
    chart_json = None
    if enriched:
        to_show = enriched[:12]
        labels = []
        for row in to_show:
            n = row['item'].component.name
            labels.append(n[:22] + '…' if len(n) > 22 else n)

        fig = go.Figure()
        for store in ALL_STORES:
            fig.add_trace(go.Bar(
                name=store,
                x=labels,
                y=[row['prices'].get(store) for row in to_show],
                marker_color=STORE_COLORS[store],
                hovertemplate='<b>%{y:,.0f} ₽</b><extra>' + store + '</extra>',
            ))
        fig.update_layout(
            barmode='group',
            yaxis_title='Цена, ₽',
            yaxis_tickformat=',d',
            plot_bgcolor='white',
            paper_bgcolor='white',
            legend=dict(orientation='h', y=1.08, x=0),
            margin=dict(t=10, b=10, l=10, r=10),
            font=dict(family='Inter, sans-serif', size=11, color='#555'),
        )
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=True, gridcolor='#f0f0f0', zeroline=False)
        chart_json = fig.to_json()

    return render(request, 'monitor/profile.html', {
        'enriched': enriched,
        'total_savings': total_savings,
        'target_reached_count': target_reached_count,
        'categories_count': len(categories_seen),
        'days_joined': days_joined,
        'ALL_STORES': ALL_STORES,
        'STORE_COLORS': STORE_COLORS,
        'chart_json': chart_json,
    })


def register_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('index')
    else:
        form = RegisterForm()
    return render(request, 'monitor/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect(request.GET.get('next', '/'))
    else:
        form = LoginForm(request)
    return render(request, 'monitor/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('index')


# ── API ────────────────────────────────────────────────────────────────────────

def api_prices(request, pk):
    component = get_object_or_404(Component, pk=pk)
    records = PriceHistory.objects.filter(component=component).select_related('store').order_by('scraped_at')
    data = [{'store': r.store.name, 'price': r.price, 'date': r.scraped_at.strftime('%Y-%m-%d')} for r in records]
    return JsonResponse({'component': component.name, 'prices': data})


def api_search(request):
    q = request.GET.get('q', '').strip()
    cat = request.GET.get('cat', '').strip()
    qs = Component.objects.select_related('category')
    if q:
        qs = qs.filter(name__icontains=q)
    if cat:
        qs = qs.filter(category__slug=cat)
    qs = _annotate_prices(qs.order_by('name'))[:30]
    results = []
    for c in qs:
        best_store, best_price = _best_deal(c.citilink_price, c.dns_price, c.mvideo_price, c.eldorado_price)
        results.append({
            'id': c.id,
            'name': c.name,
            'category': c.category.name,
            'specs': c.specs,
            'citilink': c.citilink_price,
            'dns': c.dns_price,
            'mvideo': c.mvideo_price,
            'eldorado': c.eldorado_price,
            'best_store': best_store,
            'best_price': best_price,
        })
    return JsonResponse({'results': results})


def api_parse_url(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    url = request.POST.get('url', '').strip()
    if not url:
        return JsonResponse({'error': 'URL не указан'}, status=400)
    from .scraper import parse_url
    return JsonResponse(parse_url(url))


def api_find_prices(request):
    """Find prices for a product across all stores.
    Searches local DB first (fast), then tries live scraping in parallel.
    GET ?name=<product name>
    Returns: {prices: {store: {price, source} or null}, db_name, db_id}
    """
    name = request.GET.get('name', '').strip()
    if len(name) < 3:
        return JsonResponse({'error': 'Имя слишком короткое'}, status=400)

    from django.db.models import Q
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from .scraper import STORE_SEARCH_FUNCS, SEARCH_TIMEOUT

    # Step 1: search our DB by keyword overlap (AND → OR fallback)
    words = [w for w in name.split() if len(w) > 2][:5]
    db_component = None
    db_prices = {}

    if words:
        q_and = Q()
        for w in words:
            q_and &= Q(name__icontains=w)
        db_component = Component.objects.filter(q_and).first()

        if not db_component and len(words) >= 2:
            q_or = Q()
            for w in words:
                q_or |= Q(name__icontains=w)
            db_component = Component.objects.filter(q_or).order_by('name').first()

        if db_component:
            for store_name in ALL_STORES:
                price = db_component.get_latest_price(store_name)
                if price:
                    db_prices[store_name] = {'price': price, 'source': 'db'}

    # Step 2: live scraping in parallel (best-effort)
    live_prices = {}

    def _scrape(store_name, fn):
        try:
            price = fn(name)
            return store_name, price
        except Exception:
            return store_name, None

    try:
        with ThreadPoolExecutor(max_workers=4) as ex:
            futures = {ex.submit(_scrape, s, fn): s for s, fn in STORE_SEARCH_FUNCS.items()}
            for future in as_completed(futures, timeout=SEARCH_TIMEOUT + 3):
                try:
                    store, price = future.result(timeout=1)
                    if price:
                        live_prices[store] = {'price': price, 'source': 'live'}
                except Exception:
                    pass
    except Exception:
        pass  # TimeoutError from as_completed — use whatever arrived

    # Merge: prefer live prices over DB
    prices = {}
    for store in ALL_STORES:
        if store in live_prices:
            prices[store] = live_prices[store]
        elif store in db_prices:
            prices[store] = db_prices[store]
        else:
            prices[store] = None

    return JsonResponse({
        'prices': prices,
        'db_name': db_component.name if db_component else None,
        'db_id': db_component.id if db_component else None,
    })


def api_similar(request):
    name = request.GET.get('name', '').strip()
    category_id = request.GET.get('category', '').strip()
    if len(name) < 3:
        return JsonResponse({'results': []})
    from django.db.models import Q
    qs = Component.objects.select_related('category')
    if category_id:
        qs = qs.filter(category_id=category_id)
    words = [w for w in name.split() if len(w) > 2][:5]
    if not words:
        return JsonResponse({'results': []})
    q = Q()
    for w in words:
        q |= Q(name__icontains=w)
    qs = qs.filter(q).order_by('name')[:8]
    results = [{'id': c.id, 'name': c.name, 'category': c.category.name,
                'url': f'/component/{c.id}/'} for c in qs]
    return JsonResponse({'results': results})
