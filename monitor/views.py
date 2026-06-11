import json

import pandas as pd
import plotly.graph_objects as go

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import OuterRef, Subquery, Count
from django.http import JsonResponse

from .models import Category, Store, Component, PriceHistory, Watchlist
from .forms import RegisterForm, LoginForm, WatchlistForm, ComponentSearchForm

CITILINK_COLOR = '#e85d00'
DNS_COLOR = '#005ecb'


def _annotate_prices(qs):
    latest_c = (
        PriceHistory.objects
        .filter(component=OuterRef('pk'), store__name='Citilink')
        .order_by('-scraped_at').values('price')[:1]
    )
    latest_d = (
        PriceHistory.objects
        .filter(component=OuterRef('pk'), store__name='DNS')
        .order_by('-scraped_at').values('price')[:1]
    )
    return qs.annotate(citilink_price=Subquery(latest_c), dns_price=Subquery(latest_d))


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
        row = {
            'component': c,
            'citilink': c.citilink_price,
            'dns': c.dns_price,
            'in_watchlist': c.id in watchlist_ids,
            'cheaper': '',
            'cheaper_store': '',
        }
        if c.citilink_price and c.dns_price:
            diff = c.dns_price - c.citilink_price
            if diff > 0:
                row['cheaper'] = f'Citilink −{diff:,} ₽'.replace(',', ' ')
                row['cheaper_store'] = 'citilink'
            elif diff < 0:
                row['cheaper'] = f'DNS −{abs(diff):,} ₽'.replace(',', ' ')
                row['cheaper_store'] = 'dns'
            else:
                row['cheaper'] = '='
        rows.append(row)

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
        colors = {'Citilink': CITILINK_COLOR, 'DNS': DNS_COLOR}
        fills = {'Citilink': 'rgba(232,93,0,.09)', 'DNS': 'rgba(0,94,203,.09)'}
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

    citilink_price = component.get_latest_price('Citilink')
    dns_price = component.get_latest_price('DNS')

    return render(request, 'monitor/component_detail.html', {
        'component': component,
        'citilink_price': citilink_price,
        'dns_price': dns_price,
        'plotly_json': plotly_json,
        'in_watchlist': in_watchlist,
        'watchlist_form': WatchlistForm(instance=watchlist_entry) if request.user.is_authenticated else None,
        'watchlist_entry': watchlist_entry,
    })


@login_required
def watchlist_view(request):
    items = Watchlist.objects.filter(user=request.user).select_related('component__category')
    enriched = []
    for item in items:
        citilink = item.component.get_latest_price('Citilink')
        dns = item.component.get_latest_price('DNS')
        valid = [p for p in [citilink, dns] if p is not None]
        best = min(valid) if valid else None
        enriched.append({
            'item': item,
            'citilink': citilink,
            'dns': dns,
            'best_price': best,
            'target_reached': bool(item.target_price and best and best <= item.target_price),
        })
    return render(request, 'monitor/watchlist.html', {'items': enriched})


@login_required
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
    results = [
        {
            'id': c.id,
            'name': c.name,
            'category': c.category.name,
            'specs': c.specs,
            'citilink': c.citilink_price,
            'dns': c.dns_price,
        }
        for c in qs
    ]
    return JsonResponse({'results': results})
