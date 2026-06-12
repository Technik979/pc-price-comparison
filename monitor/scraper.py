import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, quote_plus

import requests
from bs4 import BeautifulSoup

TIMEOUT = 8
SEARCH_TIMEOUT = 6
HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
}

# Suffixes to strip from og:title
_TITLE_SUFFIXES = [
    ' — Ситилинк', ' — Citilink', ' - Citilink',
    ' — DNS', ' - DNS', ' | DNS',
    ' — М.Видео', ' — МВидео', ' - М.Видео',
    ' — Эльдорадо', ' - Эльдорадо',
    ' — купить', ' - купить', ' | купить',
]


def _fetch(url, timeout=TIMEOUT):
    r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
    r.raise_for_status()
    return BeautifulSoup(r.text, 'html.parser')


def _fetch_json(url, extra_headers=None):
    h = {**HEADERS, 'Accept': 'application/json'}
    if extra_headers:
        h.update(extra_headers)
    r = requests.get(url, headers=h, timeout=SEARCH_TIMEOUT)
    r.raise_for_status()
    return r.json()


def _price_from_text(text):
    digits = re.sub(r'[^\d]', '', text or '')
    v = int(digits) if digits else None
    return v if v and 100 < v < 10_000_000 else None


def _og_price(soup):
    for prop in ('og:price:amount', 'product:price:amount'):
        m = soup.find('meta', {'property': prop})
        if m:
            return _price_from_text(m.get('content', ''))
    return None


def _og_title(soup):
    m = soup.find('meta', {'property': 'og:title'})
    t = m.get('content', '').strip() if m else ''
    if not t:
        h1 = soup.find('h1')
        t = h1.get_text(strip=True) if h1 else ''
    for suf in _TITLE_SUFFIXES:
        if suf.lower() in t.lower():
            t = t[:t.lower().index(suf.lower())].strip()
    return t or None


def _citilink(soup):
    name = _og_title(soup)
    price = _og_price(soup)
    if not price:
        for sel in ('[data-meta-price]', '.e1xnp1oc1', '.app-catalog-9gnskf'):
            el = soup.select_one(sel)
            if el:
                price = _price_from_text(el.get('data-meta-price') or el.get_text())
                if price:
                    break
    return name, price


def _dns(soup):
    name = _og_title(soup)
    price = _og_price(soup)
    if not price:
        el = soup.select_one('.price__current')
        if el:
            price = _price_from_text(el.get_text())
    return name, price


def _mvideo(soup):
    name = _og_title(soup)
    price = _og_price(soup)
    if not price:
        el = soup.select_one('.price__main-value')
        if el:
            price = _price_from_text(el.get_text())
    return name, price


def _eldorado(soup):
    name = _og_title(soup)
    price = _og_price(soup)
    if not price:
        el = soup.select_one('.price-block__final')
        if el:
            price = _price_from_text(el.get_text())
    return name, price


STORE_PARSERS = {
    'citilink.ru':  ('Citilink',  _citilink),
    'dns-shop.ru':  ('DNS',       _dns),
    'mvideo.ru':    ('М.Видео',   _mvideo),
    'eldorado.ru':  ('Эльдорадо', _eldorado),
}


def parse_url(url):
    """
    Fetch URL, detect store, extract product name + price.
    Returns dict with keys: name, price, store  OR  error.
    """
    domain = urlparse(url).netloc.lower().replace('www.', '')

    matched_store = matched_parser = None
    for d, (store_name, parser) in STORE_PARSERS.items():
        if d in domain:
            matched_store = store_name
            matched_parser = parser
            break

    if not matched_store:
        return {'error': 'Неподдерживаемый магазин. Поддерживаются: Citilink, DNS, М.Видео, Эльдорадо'}

    try:
        soup = _fetch(url)
    except requests.exceptions.Timeout:
        return {'error': 'Сайт не отвечает (таймаут). Попробуйте ещё раз.'}
    except requests.exceptions.HTTPError as e:
        return {'error': f'HTTP {e.response.status_code}: магазин вернул ошибку'}
    except Exception as e:
        return {'error': f'Не удалось загрузить страницу: {str(e)[:80]}'}

    try:
        name, price = matched_parser(soup)
    except Exception as e:
        return {'error': f'Ошибка разбора страницы: {str(e)[:80]}'}

    if not name:
        return {'error': 'Не удалось извлечь название товара. Возможно, сайт заблокировал запрос.'}

    return {'name': name, 'price': price, 'store': matched_store}


# ── Search functions: find product by name on each store's search ──────────────

def _search_citilink(name):
    soup = _fetch(f'https://www.citilink.ru/search/?text={quote_plus(name)}', timeout=SEARCH_TIMEOUT)
    for el in soup.select('[data-meta-price]'):
        price = _price_from_text(str(el.get('data-meta-price', '')))
        if price:
            return price
    for sel in ('.app-catalog-9gnskf', '.e1xnp1oc1', '.product-card__price'):
        el = soup.select_one(sel)
        if el:
            price = _price_from_text(el.get_text())
            if price:
                return price
    return None


def _search_dns(name):
    try:
        data = _fetch_json(
            f'https://www.dns-shop.ru/search/v2/results/?q={quote_plus(name)}&from=search'
        )
        products = data.get('data', {}).get('products', [])
        if products:
            p = products[0]
            price = p.get('minPrice') or p.get('price')
            return int(float(price)) if price else None
    except Exception:
        pass
    soup = _fetch(f'https://www.dns-shop.ru/search/?q={quote_plus(name)}', timeout=SEARCH_TIMEOUT)
    el = soup.select_one('.price__current, .product-card__price-current')
    return _price_from_text(el.get_text()) if el else None


def _search_mvideo(name):
    try:
        data = _fetch_json(
            f'https://www.mvideo.ru/bff/products/search-by-text-incremental'
            f'?q={quote_plus(name)}&limit=3',
            extra_headers={'Referer': 'https://www.mvideo.ru/'},
        )
        body = data.get('body', data)
        products = body.get('products', body.get('items', []))
        if products:
            p = products[0]
            pd = p.get('price', {})
            price = (pd.get('salePrice') or pd.get('basePrice') or pd.get('price')
                     if isinstance(pd, dict) else p.get('salePrice') or p.get('basePrice'))
            return int(float(price)) if price else None
    except Exception:
        pass
    return None


def _search_eldorado(name):
    for api_url in [
        f'https://www.eldorado.ru/api/search/?q={quote_plus(name)}&limit=3',
        f'https://api.eldorado.ru/v1/plp?q={quote_plus(name)}&pg=1&pageSize=3',
    ]:
        try:
            data = _fetch_json(api_url)
            items = (data.get('items') or data.get('products')
                     or data.get('data', {}).get('products', []))
            if items:
                item = items[0]
                price = (item.get('price') or item.get('currentPrice')
                         or item.get('salePrice') or item.get('regularPrice'))
                if isinstance(price, dict):
                    price = price.get('current') or price.get('value')
                return int(float(price)) if price else None
        except Exception:
            continue
    return None


STORE_SEARCH_FUNCS = {
    'Citilink':  _search_citilink,
    'DNS':       _search_dns,
    'М.Видео':   _search_mvideo,
    'Эльдорадо': _search_eldorado,
}


def search_all_stores(name):
    """Search for a product by name across all 4 stores in parallel.
    Returns: {store_name: price_int_or_None, ...}
    """
    results = {s: None for s in STORE_SEARCH_FUNCS}

    def _do(store_name, fn):
        try:
            return store_name, fn(name)
        except Exception:
            return store_name, None

    try:
        with ThreadPoolExecutor(max_workers=4) as ex:
            futures = {ex.submit(_do, s, fn): s for s, fn in STORE_SEARCH_FUNCS.items()}
            for future in as_completed(futures, timeout=SEARCH_TIMEOUT + 3):
                try:
                    store, price = future.result(timeout=1)
                    results[store] = price
                except Exception:
                    pass
    except Exception:
        pass

    return results
