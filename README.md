# PC Price Monitor

Веб-приложение на Django для сравнения цен на комплектующие ПК в магазинах **Citilink** и **DNS**.

## Возможности

- Каталог 100+ товаров с актуальными ценами из двух магазинов
- AJAX-поиск в реальном времени без перезагрузки страницы
- Интерактивный Plotly-график динамики цен за 30 дней
- Аналитика по категориям (средняя / мин / макс цена) через **Pandas**
- Авторизация: регистрация / вход / выход
- Список отслеживания с целевой ценой и индикатором «цена достигнута»
- REST API: `/api/prices/<pk>/`, `/api/search/`

## Стек

| | |
|---|---|
| Backend | Python 3.12, Django 4.x, Django REST Framework |
| Аналитика | Pandas |
| Графики | Plotly |
| Frontend | Bootstrap 5.3, JavaScript |
| БД | SQLite / PostgreSQL |

## Установка

```bash
git clone https://github.com/Technik979/pc-price-comparison.git
cd pc-price-comparison
pip install -r requirements.txt

# Создайте .env (скопируйте .env.example)
cp .env.example .env

python manage.py migrate
python manage.py update_prices --days 30
python manage.py createsuperuser
python manage.py runserver
```

Откройте http://127.0.0.1:8000/

## Структура проекта

```
pc-price-comparison/
├── config/          # Настройки Django (settings, urls, wsgi)
├── monitor/         # Основное приложение
│   ├── models.py    # Category, Store, Component, PriceHistory, Watchlist
│   ├── views.py     # Все вьюхи + API
│   ├── templates/   # HTML-шаблоны
│   ├── static/      # CSS
│   └── management/  # update_prices — команда заполнения БД
├── requirements.txt
└── TZ.md            # Техническое задание
```

## ER-диаграмма

```
User ──────────────── Watchlist ──────────────── Component
                                                     │
                                               PriceHistory
                                                     │
                                                   Store
```
