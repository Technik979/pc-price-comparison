import random
import logging

import pandas as pd
import plotly.graph_objects as go
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table, Input, Output

import db as database
import scraper

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(name)s: %(message)s')

database.init_db()
if not database.has_data():
    random.seed(42)
    scraper.seed_history(30)

CATEGORIES = ['Все'] + list(scraper.CATEGORIES.keys())
SOURCE_COLORS = {'Citilink': '#fff3cd', 'DNS': '#cfe2ff'}

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title='PC Prices',
)

app.layout = dbc.Container([

    dbc.Row(dbc.Col(
        html.H2('Сравнение цен на комплектующие ПК', className='my-3 fw-bold')
    )),

    dbc.Row([
        dbc.Col(
            dcc.Dropdown(
                id='cat-filter',
                options=[{'label': c, 'value': c} for c in CATEGORIES],
                value='Все',
                clearable=False,
            ),
            width=3,
        ),
        dbc.Col(
            dbc.Button('Обновить цены', id='scrape-btn', color='primary', n_clicks=0),
            width='auto',
        ),
        dbc.Col(
            dbc.Spinner(html.Div(id='scrape-status', className='text-muted mt-2'), size='sm'),
            width=True,
        ),
    ], className='mb-3 align-items-center'),

    dbc.Row(dbc.Col(
        dash_table.DataTable(
            id='prices-table',
            columns=[
                {'name': 'Товар',      'id': 'name'},
                {'name': 'Категория',  'id': 'category'},
                {'name': 'Магазин',    'id': 'source'},
                {'name': 'Цена, ₽',   'id': 'price',      'type': 'numeric'},
                {'name': 'Обновлено', 'id': 'scraped_at'},
            ],
            data=[],
            sort_action='native',
            filter_action='native',
            page_size=20,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '8px 12px', 'fontFamily': 'inherit'},
            style_header={'fontWeight': '600', 'backgroundColor': '#f1f3f5'},
            style_data_conditional=[
                {'if': {'filter_query': '{source} = "Citilink"'}, 'backgroundColor': '#fff8e1'},
                {'if': {'filter_query': '{source} = "DNS"'},      'backgroundColor': '#e3f2fd'},
            ],
        )
    ), className='mb-4'),

    dbc.Row(dbc.Col([
        html.Label('График динамики цен:', className='fw-semibold'),
        dcc.Dropdown(id='product-select', options=[], placeholder='Выберите товар…'),
    ], width=8), className='mb-2'),

    dbc.Row(dbc.Col(
        dcc.Graph(id='history-chart', config={'displayModeBar': True})
    )),

    dcc.Store(id='refresh-trigger'),

], fluid=True)


@app.callback(
    Output('scrape-status', 'children'),
    Output('refresh-trigger', 'data'),
    Input('scrape-btn', 'n_clicks'),
    prevent_initial_call=True,
)
def on_scrape(n_clicks):
    count, live = scraper.run_scrape()
    kind = 'живые данные' if live else 'демо-данные'
    return f'Готово: {count} позиций ({kind})', n_clicks


@app.callback(
    Output('prices-table', 'data'),
    Output('product-select', 'options'),
    Input('cat-filter', 'value'),
    Input('refresh-trigger', 'data'),
)
def update_table(category, _):
    df = database.get_latest_prices()
    if df.empty:
        return [], []
    if category != 'Все':
        df = df[df['category'] == category]
    records = df[['name', 'category', 'source', 'price', 'scraped_at']].to_dict('records')
    options = [{'label': n, 'value': n} for n in sorted(df['name'].unique())]
    return records, options


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
    colors = {'Citilink': '#f5a623', 'DNS': '#4a90d9'}
    fig = go.Figure()

    for source in df['source'].unique():
        sub = df[df['source'] == source].sort_values('scraped_at')
        fig.add_trace(go.Scatter(
            x=sub['scraped_at'],
            y=sub['price'],
            mode='lines+markers',
            name=source,
            line=dict(color=colors.get(source), width=2),
            marker=dict(size=5),
            hovertemplate='%{y:,.0f} ₽<extra>' + source + '</extra>',
        ))

    fig.update_layout(
        title=dict(text=product_name, font=dict(size=15)),
        xaxis_title='Дата',
        yaxis_title='Цена, ₽',
        yaxis_tickformat=',d',
        hovermode='x unified',
        legend=dict(orientation='h', y=1.12),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(t=60, b=40),
    )
    fig.update_xaxes(showgrid=True, gridcolor='#eee', showline=True, linecolor='#ccc')
    fig.update_yaxes(showgrid=True, gridcolor='#eee', showline=True, linecolor='#ccc')
    return fig


def _empty_fig(msg: str) -> go.Figure:
    return go.Figure().update_layout(
        annotations=[dict(text=msg, showarrow=False, font=dict(size=14, color='#888'))],
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis_visible=False,
        yaxis_visible=False,
    )


if __name__ == '__main__':
    app.run(debug=True, port=8050)
