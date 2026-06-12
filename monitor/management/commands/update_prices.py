import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from monitor.models import Category, Store, Component, PriceHistory
from monitor.data import DEMO_PRODUCTS, LAPTOP_SPECS, CATEGORY_ICONS

STORE_META = {
    'Citilink':   {'url': 'https://www.citilink.ru',   'color': '#e85d00'},
    'DNS':        {'url': 'https://www.dns-shop.ru',   'color': '#005ecb'},
    'М.Видео':    {'url': 'https://www.mvideo.ru',     'color': '#00a650'},
    'Эльдорадо':  {'url': 'https://www.eldorado.ru',   'color': '#f5a623'},
}

# Вероятность наличия товара в розничных магазинах по категории
RETAIL_PROB = {
    'Ноутбуки':           0.92,
    'Сборки ПК':          0.30,
    'Процессоры':         0.08,
    'Видеокарты':         0.08,
    'Оперативная память': 0.05,
    'SSD':                0.12,
    'Материнские платы':  0.04,
    'Кабели и провода':   0.20,
}


class Command(BaseCommand):
    help = 'Seed database with 30-day demo price history (100 products)'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing prices first')
        parser.add_argument('--days', type=int, default=30)

    def handle(self, *args, **options):
        if options['clear']:
            PriceHistory.objects.all().delete()
            self.stdout.write('Cleared price history.')

        stores = {}
        for name, meta in STORE_META.items():
            store, _ = Store.objects.get_or_create(name=name, defaults=meta)
            stores[name] = store
        self.stdout.write('Stores OK.')

        random.seed(42)
        now = timezone.now()
        days = options['days']
        total_c, total_p = 0, 0

        for cat_name, products in DEMO_PRODUCTS.items():
            cat_slug = slugify(cat_name, allow_unicode=True)
            category, _ = Category.objects.get_or_create(
                name=cat_name,
                defaults={'slug': cat_slug, 'icon': CATEGORY_ICONS.get(cat_name, '📦')},
            )

            for prod_name, base_c, base_d in products:
                specs = LAPTOP_SPECS.get(prod_name, '')
                slug = slugify(prod_name, allow_unicode=True)[:380]
                # ensure uniqueness
                n = 1
                base_slug = slug
                while Component.objects.filter(slug=slug).exclude(name=prod_name).exists():
                    slug = f'{base_slug}-{n}'
                    n += 1

                component, created = Component.objects.get_or_create(
                    name=prod_name,
                    defaults={'category': category, 'specs': specs, 'slug': slug},
                )
                if not created:
                    component.category = category
                    component.specs = specs
                    component.save()

                if options['clear'] or not component.prices.exists():
                    prob = RETAIL_PROB.get(cat_name, 0.1)
                    has_mv  = random.random() < prob
                    has_el  = random.random() < prob
                    base_mv = int(base_c * random.uniform(1.05, 1.12)) if has_mv else None
                    base_el = int(base_d * random.uniform(1.03, 1.10)) if has_el else None
                    for d in range(days, 0, -1):
                        ts = (now - timedelta(days=d)).replace(
                            hour=12, minute=0, second=0, microsecond=0
                        )
                        trend = 1 + 0.10 * (d / days) * random.choice([-1, 1])
                        noise = random.uniform(0.98, 1.02)
                        PriceHistory.objects.create(
                            component=component, store=stores['Citilink'],
                            price=int(base_c * trend * noise), scraped_at=ts,
                        )
                        PriceHistory.objects.create(
                            component=component, store=stores['DNS'],
                            price=int(base_d * trend * noise), scraped_at=ts,
                        )
                        if has_mv:
                            PriceHistory.objects.create(
                                component=component, store=stores['М.Видео'],
                                price=int(base_mv * trend * random.uniform(0.99, 1.01)),
                                scraped_at=ts,
                            )
                        if has_el:
                            PriceHistory.objects.create(
                                component=component, store=stores['Эльдорадо'],
                                price=int(base_el * trend * random.uniform(0.99, 1.01)),
                                scraped_at=ts,
                            )
                        total_p += 2 + int(has_mv) + int(has_el)
                total_c += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done: {total_c} components, {total_p} price records.'
        ))
