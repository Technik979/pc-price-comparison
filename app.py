import random
import logging

import pandas as pd
import plotly.graph_objects as go
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table, Input, Output, State, ALL, ctx

import db as database
import scraper

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(name)s: %(message)s')

database.init_db()
if not database.has_data():
    random.seed(42)
    scraper.seed_history(30)

CATEGORIES = ['Все'] + list(scraper.CATEGORIES.keys())
CAT_ICONS = {
    'Все':               '🔍',
    'Процессоры':        '⚡',
    'Видеокарты':        '🎮',
    'Оперативная память':'💾',
    'SSD':               '💿',
    'Материнские платы': '🔧',
    'Ноутбуки':          '💻',
    'Сборки ПК':         '🖥️',
    'Кабели и провода':  '🔌',
}
CITILINK = '#e85d00'
DNS      = '#005ecb'

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title='PC Price Monitor',
)

# ── Layout ─────────────────────────────────────────────────────────────────────

app.layout = html.Div([

    # ── Hero ──────────────────────────────────────────────────────────────────
    html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col(html.Div([
                    html.H1('🖥️ PC Price Monitor'),
                    html.P('Сравнение цен — Citilink vs DNS', className='sub'),
                ], className='hero-inner'), width=8),
                dbc.Col(html.Div([
                    dbc.Button('↻  Обновить цены', id='scrape-btn',
                               className='update-btn', n_clicks=0),
                    dbc.Spinner(
                        html.Div(id='scrape-status',
                                 style={'color': 'rgba(255,255,255,.5)',
                                        'fontSize': '.8rem', 'marginTop': '7px'}),
                        size='sm', color='light',
                    ),
                ], style={'textAlign': 'right'}), width=4,
                    className='d-flex flex-column justify-content-center'),
            ])
        ], fluid=True),
    ], className='hero'),

    dbc.Container([

        # ── Stat cards ────────────────────────────────────────────────────────
        dbc.Row([
            dbc.Col(html.Div([
                html.Div('📦', className='stat-icon'),
                html.Div([
                    html.Div(id='stat-total', className='stat-num'),
                    html.Div('товаров', className='stat-lbl'),
                ]),
            ], className='stat-card c1'), md=3, xs=6, className='mb-3'),

            dbc.Col(html.Div([
                html.Div('📂', className='stat-icon'),
                html.Div([
                    html.Div(id='stat-cats', className='stat-num'),
                    html.Div('категорий', className='stat-lbl'),
                ]),
            ], className='stat-card c2'), md=3, xs=6, className='mb-3'),

            dbc.Col(html.Div([
                html.Div('🏪', className='stat-icon'),
                html.Div([
                    html.Div('2', className='stat-num'),
                    html.Div('магазина', className='stat-lbl'),
                ]),
            ], className='stat-card c3'), md=3, xs=6, className='mb-3'),

            dbc.Col(html.Div([
                html.Div('💰', className='stat-icon'),
                html.Div([
                    html.Div(id='stat-min', className='stat-num',
                             style={'fontSize': '1.3rem'}),
                    html.Div('мин. цена', className='stat-lbl'),
                ]),
            ], className='stat-card c4'), md=3, xs=6, className='mb-3'),
        ], className='g-3 mb-2'),

        # ── Comparison table ──────────────────────────────────────────────────
        html.Div([
            html.Div('Сравнение цен', className='section-title'),

            # Category pills
            html.Div([
                html.Span(
                    f'{CAT_ICONS.get(c, "")} {c}',
                    id={'type': 'cat-pill', 'index': c},
                    className='cat-pill' + (' active' if c == 'Все' else ''),
                    n_clicks=0,
                )
                for c in CATEGORIES
            ], className='mb-3'),

            dash_table.DataTable(
                id='prices-table',
                columns=[
                    {'name': 'Товар',          'id': 'name'},
                    {'name': 'Категория',       'id': 'category'},
                    {'name': 'Citilink, ₽',    'id': 'Citilink',   'type': 'numeric'},
                    {'name': 'DNS, ₽',          'id': 'DNS',        'type': 'numeric'},
                    {'name': 'Выгоднее',        'id': 'выгоднее'},
                ],
                data=[],
                sort_action='native',
                filter_action='native',
                page_size=20,
                style_table={'overflowX': 'auto', 'borderRadius': '10px',
                             'overflow': 'hidden'},
                style_cell={
                    'textAlign': 'left', 'padding': '11px 16px',
                    'border': '1px solid #f2f4f8', 'whiteSpace': 'normal',
                    'maxWidth': '340px',
                },
                style_header={
                    'fontWeight': '700', 'backgroundColor': '#f8f9fb',
                    'color': '#444', 'border': '1px solid #ebebeb',
                },
                style_data_conditional=[
                    {'if': {'row_index': 'odd'}, 'backgroundColor': '#fafbfd'},
                    {'if': {'column_id': 'Citilink'},
                     'color': CITILINK, 'fontWeight': '700'},
                    {'if': {'column_id': 'DNS'},
                     'color': DNS, 'fontWeight': '700'},
                    {'if': {'column_id': 'name'},
                     'fontWeight': '500', 'color': '#1a1a2e'},
                    {'if': {'filter_query': '{cheaper_store} = "Citilink"',
                            'column_id': 'выгоднее'},
                     'color': '#c44f00', 'fontWeight': '600'},
                    {'if': {'filter_query': '{cheaper_store} = "DNS"',
                            'column_id': 'выгоднее'},
                     'color': '#0050a8', 'fontWeight': '600'},
                ],
            ),
        ], className='section-card'),

        # ── Price history chart ───────────────────────────────────────────────
        html.Div([
            html.Div('Динамика цен', className='section-title'),
            dbc.Row([
                dbc.Col(
                    dcc.Dropdown(id='product-select', options=[],
                                 placeholder='Выберите товар…'),
                    md=7,
                ),
            ], className='mb-3'),
            dcc.Graph(id='history-chart', config={'displayModeBar': True}),
        ], className='section-card'),

    ], fluid=True),

    dcc.Store(id='refresh-trigger'),
    dcc.Store(id='active-cat', data='Все'),
])


# ── Callbacks ──────────────────────────────────────────────────────────────────

@app.callback(
    Output('scrape-status', 'children'),
    Output('refresh-trigger', 'data'),
    Input('scrape-btn', 'n_clicks'),
    prevent_initial_call=True,
)
def on_scrape(n):
    count, live = scraper.run_scrape()
    kind = 'живые данные' if live else 'демо-данные'
    return f'Обновлено: {count} поз. ({kind})', n


@app.callback(
    Output('active-cat', 'data'),
    Output({'type': 'cat-pill', 'index': ALL}, 'className'),
    Input({'type': 'cat-pill', 'index': ALL}, 'n_clicks'),
    State({'type': 'cat-pill', 'index': ALL}, 'id'),
    prevent_initial_call=True,
)
def switch_category(_, ids):
    triggered = ctx.triggered_id
    if not triggered:
        return 'Все', ['cat-pill'] * len(ids)
    active = triggered['index']
    return active, [
        'cat-pill active' if d['index'] == active else 'cat-pill'
        for d in ids
    ]


@app.callback(
    Output('prices-table', 'data'),
    Output('prices-table', 'columns'),
    Output('product-select', 'options'),
    Output('stat-total', 'children'),
    Output('stat-cats', 'children'),
    Output('stat-min', 'children'),
    Input('active-cat', 'data'),
    Input('refresh-trigger', 'data'),
)
def update_table(category, _):
    df = database.get_price_comparison()
    if df.empty:
        cols = [{'name': c, 'id': c} for c in ['name', 'category', 'Citilink', 'DNS', 'выгоднее']]
        return [], cols, [], '—', '—', '—'

    # Stats from full dataset
    total = df['name'].nunique()
    cats  = df['category'].nunique()
    prices = []
    for col in ('Citilink', 'DNS'):
        if col in df.columns:
            prices.extend(df[col].dropna().tolist())
    min_price = f'{int(min(prices)):,} ₽'.replace(',', ' ') if prices else '—'

    if category != 'Все':
        df = df[df['category'] == category]

    # Build columns dynamically (DNS/Citilink may not exist if only one source)
    present_sources = [c for c in ('Citilink', 'DNS') if c in df.columns]
    show_specs = (category == 'Ноутбуки')
    columns = [
        {'name': 'Товар',     'id': 'name'},
        {'name': 'Категория', 'id': 'category'},
        *([{'name': 'Характеристики', 'id': 'specs'}] if show_specs else []),
        *[{'name': f'{s}, ₽', 'id': s, 'type': 'numeric'} for s in present_sources],
        {'name': 'Выгоднее',  'id': 'выгоднее'},
    ]

    show_cols = ['name', 'category'] + (['specs'] if show_specs else []) + present_sources + ['выгоднее', 'cheaper_store']
    records   = df[[c for c in show_cols if c in df.columns]].to_dict('records')

    options = [{'label': f'{CAT_ICONS.get(row["category"], "")} {row["name"]}',
                'value': row['name']}
               for _, row in df.iterrows()]

    return records, columns, options, str(total), str(cats), min_price


@app.callback(
    Output('history-chart', 'figure'),
    Input('product-select', 'value'),
)
def update_chart(product_name):
    if not product_name:
        return _empty_fig('Выберите товар для графика')

    df = database.get_price_history(product_name)
    if df.empty:
        return _empty_fig('Нет данных')

    df['scraped_at'] = pd.to_datetime(df['scraped_at'])
    colors = {'Citilink': CITILINK, 'DNS': DNS}
    fills  = {'Citilink': 'rgba(232,93,0,.08)', 'DNS': 'rgba(0,94,203,.08)'}

    fig = go.Figure()
    for source in df['source'].unique():
        sub = df[df['source'] == source].sort_values('scraped_at')
        c   = colors.get(source, '#888')
        fig.add_trace(go.Scatter(
            x=sub['scraped_at'], y=sub['price'],
            mode='lines+markers', name=source,
            line=dict(color=c, width=2.5),
            marker=dict(size=6, color=c, line=dict(width=1.5, color='white')),
            fill='tozeroy', fillcolor=fills.get(source, 'rgba(0,0,0,.05)'),
            hovertemplate='<b>%{y:,.0f} ₽</b>  %{x|%d.%m.%Y}<extra>' + source + '</extra>',
        ))

    fig.update_layout(
        title=dict(text=f'<b>{product_name}</b>',
                   font=dict(size=14, color='#1a1a2e'), x=0),
        xaxis_title=None, yaxis_title='Цена, ₽',
        yaxis_tickformat=',d',
        hovermode='x unified',
        legend=dict(orientation='h', y=1.1, x=0, font=dict(size=12)),
        plot_bgcolor='white', paper_bgcolor='white',
        margin=dict(t=55, b=30, l=10, r=10),
        font=dict(family='Inter, sans-serif', size=12, color='#555'),
    )
    fig.update_xaxes(showgrid=False, showline=True, linecolor='#f0f0f0',
                     tickfont=dict(color='#aaa'))
    fig.update_yaxes(showgrid=True, gridcolor='#f5f5f5', zeroline=False,
                     showline=False, tickfont=dict(color='#aaa'))
    return fig


def _empty_fig(msg: str) -> go.Figure:
    return go.Figure().update_layout(
        annotations=[dict(text=msg, showarrow=False,
                          font=dict(size=14, color='#ccc'))],
        plot_bgcolor='white', paper_bgcolor='white',
        xaxis_visible=False, yaxis_visible=False,
        margin=dict(t=20, b=20),
    )


if __name__ == '__main__':
    app.run(debug=True, port=8050)
