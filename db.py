import os
import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'prices.db')


def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS products (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT NOT NULL,
            category TEXT NOT NULL,
            url      TEXT DEFAULT '',
            source   TEXT NOT NULL,
            specs    TEXT DEFAULT '',
            UNIQUE(name, source)
        );
        CREATE TABLE IF NOT EXISTS prices (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL REFERENCES products(id),
            price      INTEGER NOT NULL,
            scraped_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_prices_product ON prices(product_id);
        CREATE INDEX IF NOT EXISTS idx_prices_date    ON prices(scraped_at);
    ''')
    conn.commit()
    conn.close()


def upsert_product(name: str, category: str, url: str, source: str, specs: str = '') -> int:
    conn = get_conn()
    conn.execute('''
        INSERT INTO products (name, category, url, source, specs)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(name, source) DO UPDATE SET
            category = excluded.category,
            url      = excluded.url,
            specs    = excluded.specs
    ''', (name, category, url, source, specs))
    conn.commit()
    row = conn.execute(
        'SELECT id FROM products WHERE name = ? AND source = ?', (name, source)
    ).fetchone()
    conn.close()
    return row['id']


def add_price(product_id: int, price: int, scraped_at: str = None):
    if scraped_at is None:
        scraped_at = datetime.now().isoformat(timespec='seconds')
    conn = get_conn()
    conn.execute(
        'INSERT INTO prices (product_id, price, scraped_at) VALUES (?, ?, ?)',
        (product_id, price, scraped_at),
    )
    conn.commit()
    conn.close()


def get_price_comparison() -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql_query('''
        SELECT p.name, p.category, p.source, pr.price, p.specs
        FROM prices pr
        JOIN products p ON p.id = pr.product_id
        WHERE pr.id IN (SELECT MAX(id) FROM prices GROUP BY product_id)
    ''', conn)
    conn.close()
    if df.empty:
        return pd.DataFrame()

    specs_map = df.groupby('name')['specs'].first()

    pivot = df.pivot_table(
        index=['name', 'category'], columns='source', values='price'
    ).reset_index()
    pivot.columns.name = None
    pivot['specs'] = pivot['name'].map(specs_map)

    if 'Citilink' in pivot.columns and 'DNS' in pivot.columns:
        diff = pivot['DNS'] - pivot['Citilink']
        def _label(d):
            if pd.isna(d): return '—'
            d = int(d)
            if d > 0:  return f'Citilink  −{d:,} ₽'.replace(',', ' ')
            if d < 0:  return f'DNS  −{-d:,} ₽'.replace(',', ' ')
            return '='
        pivot['выгоднее']     = diff.apply(_label)
        pivot['cheaper_store'] = diff.apply(
            lambda d: '' if pd.isna(d) else ('Citilink' if d > 0 else ('DNS' if d < 0 else 'equal'))
        )

    return pivot.sort_values(['category', 'name']).reset_index(drop=True)


def get_price_history(product_name: str) -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql_query('''
        SELECT p.name, p.source, pr.price, pr.scraped_at
        FROM prices pr
        JOIN products p ON p.id = pr.product_id
        WHERE p.name = ?
        ORDER BY pr.scraped_at
    ''', conn, params=(product_name,))
    conn.close()
    return df


def get_product_names() -> list:
    conn = get_conn()
    rows = conn.execute('SELECT DISTINCT name FROM products ORDER BY name').fetchall()
    conn.close()
    return [r['name'] for r in rows]


def has_data() -> bool:
    conn = get_conn()
    count = conn.execute('SELECT COUNT(*) FROM prices').fetchone()[0]
    conn.close()
    return count > 0
