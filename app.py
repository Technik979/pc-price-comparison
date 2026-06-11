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
CITILINK_COLOR = '#e85d00'
DNS_COLOR      = '#005ecb'

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title='PC Price Monitor',
)

# ── Layout ────────────────────────────────────────────────────────────────────

app.layout = html.Div([

    # Hero header
    html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H1('🖥️ PC Price Monitor'),
                    html.P('Сравнение цен на комплектующие — Citilink vs DNS'),
                ], width=8),
                dbc.Col([
                    html.Div([
                        dbc.Button('↻  Обновить цены', id='scrape-btn',
                                   className='update-btn', n_clicks=0),
                        dbc.Spinner(
                            html.Div(id='scrape-status',
                                     style={'color': 'rgba(255,255,255,.6)',
                                            'fontSize': '.82rem', 'marginTop': '6px'}),
                            size='sm', color='light',
                        ),
                    ], style={'textAlign': 'right'}),
                ], width=4, className='d-flex align-items-center justify-content-end'),
            ])
        ], fluid=True),
    ], className='hero'),

    dbc.Container([

        # Stat cards
        dbc.Row([
            dbc.Col(html.Div([
                html.Div(id='stat-total',      className='stat-num stat-accent'),
                html.Div('товаров',            className='stat-lbl'),
            ], className='stat-card'), md=3, xs=6),
            dbc.Col(html.Div([
                html.Div(id='stat-cats',       className='stat-num stat-accent'),
                html.Div('категорий',          className='stat-lbl'),
            ], className='stat-card'), md=3, xs=6),
            dbc.Col(html.Div([
                html.Div('2',                  className='stat-num stat-accent'),
                html.Div('магазина',           className='stat-lbl'),
            ], className='stat-card'), md=3, xs=6),
            dbc.Col(html.Div([
                html.Div(id='stat-min',        className='stat-num', style={'fontSize': '1.3rem'}),
                html.Div('минимальная цена',   className='stat-lbl'),
            ], className='stat-card'), md=3, xs=6),
        ], className='g-3 mb-4'),

        # Table section
        html.Div([
            html.Div('Текущие цены', className='section-title'),

            # Category pills
            html.Div(
                [html.Span(c, id={'type': 'cat-pill', 'index': c},
                           className='cat-pill' + (' active' if c == 'Все' else ''),
                           n_clicks=0)
                 for c in CATEGORIES],
                className='mb-3',
            ),

            dash_table.DataTable(
                id='prices-table',
                columns=[
                    {'name': 'Товар',      'id': 'name'},
                    {'name': 'Категория',  'id': 'category'},
                    {'name': 'Магазин',    'id': 'source'},
                    {'name': 'Цена, ₽',   'id': 'price', 'type': 'numeric'},
                    {'name': 'Обновлено', 'id': 'scraped_at'},
                ],
                data=[],
                sort_action='native',
                filter_action='native',
                page_size=20,
                style_table={'overflowX': 'auto', 'borderRadius': '10px', 'overflow': 'hidden'},
                style_cell={
                    'textAlign': 'left', 'padding': '11px 16px',
                    'border': '1px solid #f2f2f2', 'whiteSpace': 'normal',
                },
                style_header={
                    'fontWeight': '700', 'backgroundColor': '#f8f9fb',
                    'color': '#333', 'border': '1px solid #ebebeb',
                },
                style_data_conditional=[
                    {'if': {'row_index': 'odd'}, 'backgroundColor': '#fafafa'},
                    {'if': {'filter_query': '{source} = "Citilink"', 'column_id': 'source'},
                     'color': CITILINK_COLOR, 'fontWeight': '700'},
                    {'if': {'filter_query': '{source} = "DNS"', 'column_id': 'source'},
                     'color': DNS_COLOR, 'fontWeight': '700'},
                    {'if': {'column_id': 'price'}, 'fontWeight': '600', 'color': '#1a1a2e'},
                ],
            ),
        ], className='section-card'),

        # Chart section
        html.Div([
            html.Div('Динамика цен', className='section-title'),
            dbc.Row([
                dbc.Col(
                    dcc.Dropdown(
                        id='product-select', options=[],
                        placeholder='Выберите товар…',
                    ),
                    md=7,
                ),
            ], className='mb-3'),
            dcc.Graph(id='history-chart', config={'displayModeBar': True},
                      style={'borderRadius': '10px', 'overflow': 'hidden'}),
        ], className='section-card'),

    ], fluid=True),

    dcc.Store(id='refresh-trigger'),
    dcc.Store(id='active-cat', data='Все'),
])


# ── Callbacks ─────────────────────────────────────────────────────────────────

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
    classes = [('cat-pill active' if d['index'] == active else 'cat-pill') for d in ids]
    return active, classes


@app.callback(
    Output('prices-table', 'data'),
    Output('product-select', 'options'),
    Output('stat-total', 'children'),
    Output('stat-cats', 'children'),
    Output('stat-min', 'children'),
    Input('active-cat', 'data'),
    Input('refresh-trigger', 'data'),
)
def update_table(category, _):
    df = database.get_latest_prices()
    if df.empty:
        return [], [], '—', '—', '—'

    total_products = df['name'].nunique()
    total_cats     = df['category'].nunique()
    min_price      = df['price'].min()
    min_label      = f'{int(min_price):,} ₽'.replace(',', ' ')

    if category != 'Все':
        df = df[df['category'] == category]

    records = df[['name', 'category', 'source', 'price', 'scraped_at']].to_dict('records')
    options = [{'label': n, 'value': n} for n in sorted(df['name'].unique())]
    return records, options, str(total_products), str(total_cats), min_label


@app.callback(
    Output('history-chart', 'figure'),
    Input('product-select', 'value'),
)
def update_chart(product_name):
    if not product_name:
        return _empty_fig('Выберите товар для отображения истории цен')

    df = database.get_price_history(product_name)
    if df.empty:
        return _empty_fig('Нет данных')

    df['scraped_at'] = pd.to_datetime(df['scraped_at'])
    colors = {'Citilink': CITILINK_COLOR, 'DNS': DNS_COLOR}
    fills  = {'Citilink': 'rgba(232,93,0,.08)', 'DNS': 'rgba(0,94,203,.08)'}

    fig = go.Figure()
    for source in df['source'].unique():
        sub = df[df['source'] == source].sort_values('scraped_at')
        color = colors.get(source, '#888')
        fig.add_trace(go.Scatter(
            x=sub['scraped_at'], y=sub['price'],
            mode='lines+markers', name=source,
            line=dict(color=color, width=2.5),
            marker=dict(size=6, color=color,
                        line=dict(width=1.5, color='white')),
            fill='tozeroy',
            fillcolor=fills.get(source, 'rgba(0,0,0,.04)'),
            hovertemplate='<b>%{y:,.0f} ₽</b><br>%{x|%d.%m.%Y}<extra>' + source + '</extra>',
        ))

    fig.update_layout(
        title=dict(text=f'<b>{product_name}</b>', font=dict(size=14, color='#1a1a2e'), x=0),
        xaxis_title=None, yaxis_title='Цена, ₽',
        yaxis_tickformat=',d',
        hovermode='x unified',
        legend=dict(orientation='h', y=1.1, x=0),
        plot_bgcolor='white', paper_bgcolor='white',
        margin=dict(t=50, b=30, l=10, r=10),
        font=dict(family='Inter, sans-serif', size=12),
    )
    fig.update_xaxes(showgrid=False, showline=True, linecolor='#eee', tickfont=dict(color='#999'))
    fig.update_yaxes(showgrid=True, gridcolor='#f0f0f0', zeroline=False,
                     showline=False, tickfont=dict(color='#999'))
    return fig


def _empty_fig(msg: str) -> go.Figure:
    return go.Figure().update_layout(
        annotations=[dict(text=msg, showarrow=False, font=dict(size=14, color='#bbb'))],
        plot_bgcolor='white', paper_bgcolor='white',
        xaxis_visible=False, yaxis_visible=False,
        margin=dict(t=20, b=20),
    )


if __name__ == '__main__':
    app.run(debug=True, port=8050)
