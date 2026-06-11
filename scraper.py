import re
import time
import logging
import random
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

import db as database

logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'ru-RU,ru;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

CATEGORIES = {
    'Процессоры': {
        'citilink': 'processory',
        'dns': '17a8a01d16404e77/processory',
    },
    'Видеокарты': {
        'citilink': 'videokarty',
        'dns': '17a8929716404e77/videokarty',
    },
    'Оперативная память': {
        'citilink': 'moduli-pamyati',
        'dns': '17a8a11d16404e77/moduli-pamyati',
    },
    'SSD': {
        'citilink': 'ssd-nakopiteli',
        'dns': '17a8937b16404e77/ssd-nakopiteli',
    },
    'Материнские платы': {
        'citilink': 'materinskie-platy',
        'dns': '17a8a16716404e77/materinskie-platy',
    },
    'Ноутбуки': {
        'citilink': 'noutbuki',
        'dns': '17a8971f16404e77/noutbuki',
    },
    'Сборки ПК': {
        'citilink': 'gotovye-kompyutery',
        'dns': '17a891f016404e77/personalnye-kompyutery',
    },
    'Кабели и провода': {
        'citilink': 'kabeli-i-perekhodniki',
        'dns': '17a8a05316404e77/kabeli-i-adaptery',
    },
}

# Base prices: (name, citilink_price, dns_price)
DEMO_PRODUCTS = {
    'Процессоры': [
        ('AMD Ryzen 5 5600X',       15990, 16490),
        ('Intel Core i5-12400F',    14290, 14790),
        ('AMD Ryzen 7 5800X3D',     27990, 28490),
        ('Intel Core i7-13700K',    31490, 32090),
        ('AMD Ryzen 9 7950X',       53990, 54990),
    ],
    'Видеокарты': [
        ('NVIDIA GeForce RTX 4060 8GB',   34490, 34990),
        ('AMD Radeon RX 7600 8GB',        28990, 29490),
        ('NVIDIA GeForce RTX 4070 12GB',  58990, 59990),
        ('AMD Radeon RX 7900 XTX 24GB',   79990, 81490),
        ('NVIDIA GeForce RTX 4090 24GB', 149990, 152990),
    ],
    'Оперативная память': [
        ('Kingston FURY Beast DDR4 16GB 3200MHz',  3490,  3590),
        ('Corsair Vengeance DDR5 32GB 5600MHz',    8790,  8990),
        ('G.Skill Trident Z5 DDR5 64GB 6000MHz',  19490, 19990),
        ('Kingston ValueRAM DDR4 8GB 3200MHz',     1790,  1890),
        ('Crucial Pro DDR5 32GB 4800MHz',          7290,  7490),
    ],
    'SSD': [
        ('Samsung 870 EVO 1TB SATA',       8490,  8790),
        ('WD Black SN850X 1TB NVMe',       8290,  8590),
        ('Kingston KC3000 2TB NVMe',      12490, 12990),
        ('Crucial MX500 500GB SATA',       4290,  4490),
        ('Seagate FireCuda 530 2TB NVMe', 14490, 14990),
    ],
    'Материнские платы': [
        ('ASUS ROG STRIX B550-F GAMING',         14990, 15490),
        ('MSI MAG B660 TOMAHAWK DDR4',            12490, 12990),
        ('Gigabyte B450M DS3H',                    4990,  5290),
        ('ASRock X670E Taichi',                   39990, 40990),
        ('ASUS PRIME Z790-P DDR5',                21990, 22490),
    ],
    'Ноутбуки': [
        ('Acer Aspire 3 A315 Ryzen 3 7320U 8GB',         29990,  30990),
        ('Lenovo IdeaPad 1 15AMN7 Ryzen 5 8GB',          34990,  35990),
        ('HP Pavilion 15 i5-1235U 8GB 512GB',            44990,  45990),
        ('Lenovo IdeaPad 3 Ryzen 5 5500U 16GB',          46990,  47990),
        ('ASUS VivoBook 15 i5-1235U 16GB 512GB',         54990,  55990),
        ('Huawei MateBook D15 i5-1235U 16GB',            49990,  51490),
        ('Dell Inspiron 15 3530 i5-1334U 16GB',          52990,  53990),
        ('Xiaomi RedmiBook Pro 14 i7-13700H 16GB',       69990,  71490),
        ('Lenovo ThinkPad E16 i5-1335U 16GB 512GB',      64990,  66490),
        ('ASUS ZenBook 14 OLED i7-1360P 16GB',           84990,  86490),
        ('Acer Nitro 5 AN515 i7-12700H RTX 4060 16GB',   89990,  91490),
        ('Lenovo Legion 5 Ryzen 7 7745HX RTX 4070',     109990, 111990),
        ('MSI Katana 15 i7-12650H RTX 4070 16GB',       119990, 121490),
        ('Apple MacBook Air M2 8GB 256GB',                99990, 101990),
        ('Apple MacBook Pro 14 M3 Pro 18GB 512GB',      199990, 203990),
        ('ASUS ROG Strix G16 i9-13980HX RTX 4080',      189990, 192990),
    ],
    'Сборки ПК': [
        ('Офисная: Ryzen 3 4100 + 8GB DDR4 + SSD 256GB',          19990,  20990),
        ('Тихая: Ryzen 5 5600G встр. + 16GB DDR4 + SSD 512GB',    29990,  31490),
        ('Начальная: i3-12100F + GTX 1660S 16GB + SSD 512GB',     44990,  46490),
        ('1080p Средняя: i5-12400F + RX 7600 16GB DDR4',          64990,  66490),
        ('1080p Игровая: Ryzen 5 5600 + RTX 4060 16GB DDR4',      74990,  76990),
        ('1080p+: Ryzen 5 7600 + RTX 4060 Ti 16GB DDR5',          94990,  96990),
        ('1440p: i7-13700F + RTX 4070 32GB DDR5',                 134990, 137490),
        ('1440p PRO: Ryzen 7 7700X + RTX 4070 Super 32GB',        154990, 157990),
        ('4K Игровая: i7-13700K + RTX 4080 32GB DDR5',            219990, 223990),
        ('Стрим: i9-13900K + RTX 4070 Ti + 64GB DDR5',            239990, 244990),
        ('Энтузиаст: Ryzen 9 7950X + RTX 4090 64GB DDR5',         389990, 395990),
        ('Рабочая станция: Ryzen 9 7950X + 128GB ECC + 4TB NVMe', 299990, 305990),
    ],
    'Кабели и провода': [
        ('Кабель HDMI 2.1 2м Buro',                 590,    690),
        ('DisplayPort 1.4 1.8м Telecom',             890,    990),
        ('USB-C — USB-C 1м 100W Baseus',            1290,   1390),
        ('Патч-корд UTP Cat6 3м Cablexpert',         290,    350),
        ('Кабель питания ATX 24pin 30см Akasa',      590,    650),
    ],
}


def _parse_citilink(slug: str, category: str) -> list[dict]:
    try:
        resp = requests.get(
            f'https://www.citilink.ru/catalog/{slug}/',
            headers=HEADERS, timeout=15,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        products = []
        for card in soup.select('[data-meta="product"]')[:8]:
            name_el = card.select_one('a[class*="name"]') or card.select_one('a[class*="Name"]')
            price_el = (
                card.select_one('[class*="price_current"]')
                or card.select_one('[class*="price-current"]')
                or card.select_one('[class*="Price_"]')
            )
            if not name_el or not price_el:
                continue
            price_text = re.sub(r'[^\d]', '', price_el.get_text())
            if not price_text:
                continue
            href = name_el.get('href', '')
            products.append({
                'name': name_el.get_text(strip=True),
                'category': category,
                'price': int(price_text),
                'url': ('https://www.citilink.ru' + href) if href.startswith('/') else href,
                'source': 'Citilink',
            })
        logger.info('Citilink %s: %d items', category, len(products))
        return products
    except Exception as e:
        logger.warning('Citilink failed (%s): %s', category, e)
        return []


def _parse_dns(path: str, category: str) -> list[dict]:
    try:
        resp = requests.get(
            f'https://www.dns-shop.ru/catalog/{path}/',
            headers=HEADERS, timeout=15,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        products = []
        for card in (soup.select('.catalog-product') or soup.select('[data-id]'))[:8]:
            name_el = (
                card.select_one('.catalog-product__name a')
                or card.select_one('a[class*="name"]')
            )
            price_el = (
                card.select_one('.product-buy__price')
                or card.select_one('[class*="price"]')
            )
            if not name_el or not price_el:
                continue
            price_text = re.sub(r'[^\d]', '', price_el.get_text())
            if not price_text:
                continue
            href = name_el.get('href', '')
            products.append({
                'name': name_el.get_text(strip=True),
                'category': category,
                'price': int(price_text),
                'url': ('https://www.dns-shop.ru' + href) if href.startswith('/') else href,
                'source': 'DNS',
            })
        logger.info('DNS %s: %d items', category, len(products))
        return products
    except Exception as e:
        logger.warning('DNS failed (%s): %s', category, e)
        return []


def _demo_snapshot(category: str) -> list[dict]:
    result = []
    for name, price_c, price_d in DEMO_PRODUCTS.get(category, []):
        jitter = lambda p: int(p * random.uniform(0.97, 1.03))
        result.append({'name': name, 'category': category, 'price': jitter(price_c), 'url': '', 'source': 'Citilink'})
        result.append({'name': name, 'category': category, 'price': jitter(price_d), 'url': '', 'source': 'DNS'})
    return result


def seed_history(days: int = 30):
    """Populate DB with simulated price history for the past N days."""
    now = datetime.now()
    for category, products in DEMO_PRODUCTS.items():
        for name, base_c, base_d in products:
            pid_c = database.upsert_product(name, category, '', 'Citilink')
            pid_d = database.upsert_product(name, category, '', 'DNS')
            for d in range(days, 0, -1):
                ts = (now - timedelta(days=d)).replace(
                    hour=12, minute=0, second=0, microsecond=0
                ).isoformat(timespec='seconds')
                trend = 1 + 0.10 * (d / days) * random.choice([-1, 1])
                noise = random.uniform(0.98, 1.02)
                database.add_price(pid_c, int(base_c * trend * noise), ts)
                database.add_price(pid_d, int(base_d * trend * noise), ts)


def run_scrape() -> tuple[int, bool]:
    """Scrape all categories. Falls back to demo data if live scraping fails.
    Returns (total items saved, live_data_used)."""
    all_products: list[dict] = []
    live = False

    for cat, slugs in CATEGORIES.items():
        citilink = _parse_citilink(slugs['citilink'], cat)
        dns = _parse_dns(slugs['dns'], cat)
        if citilink or dns:
            live = True
            all_products.extend(citilink + dns)
        else:
            all_products.extend(_demo_snapshot(cat))
        time.sleep(0.3)

    now = datetime.now().isoformat(timespec='seconds')
    for p in all_products:
        pid = database.upsert_product(p['name'], p['category'], p['url'], p['source'])
        database.add_price(pid, p['price'], now)

    return len(all_products), live
