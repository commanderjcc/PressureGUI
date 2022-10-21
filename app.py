# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import pandas as pd
from dash import Dash, dcc, html, dash_table
from dash.dependencies import Output, Input, State
from dash_extensions.enrich import Output, DashProxy, Input, MultiplexerTransform
import dash_bootstrap_components as dbc
import plotly.express as px
import json
import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import sqlite3
from run_query import get_pressure, get_discharge

# Declare the database file name here
db_name = "copy.db"

# app = Dash(external_stylesheets=[dbc.themes.FLATLY])
app = DashProxy(external_stylesheets=[dbc.themes.FLATLY],
                prevent_initial_callbacks=True, transforms=[MultiplexerTransform()])

app.layout = dbc.Container([
    dcc.Store(id='memory-output'),
    dbc.Row([
        dbc.Col(
            dbc.Card([
                html.H2("Abbott Lab GUI"),
                html.H5("Coolness overload")
            ], body="true", color="light"), width={"size": 10, "offset": 1})
    ]),
    html.Hr(),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                html.H5("Run Site Query"),
                html.P("Site ID:"),
                dcc.Dropdown(
                    options=['BEN', 'BLI', 'BSL', 'CLE', 'CRB', 'DAI', 'DFF', 'DFL', 'DFM', 'DFU', 'HCL',
                             'HCN', 'HCS', 'IND', 'LAK', 'LDF', 'MIT', 'NEB', 'PBC', 'SBL', 'SFL', 'SHE',
                             'SOL', 'STR', 'TCU', 'TIE', 'WAN'],
                    value='BEN',
                    id='site_id',
                    style={'display': 'inline-block', "margin": "5px"}),
                dbc.Button("Query Site", id="query", color="primary",
                           style={'display': 'inline-block', "margin": "5px"},
                           n_clicks=0)
            ], body="true", color="light"),
            html.Hr(),
            dbc.Card([
                html.H5("Make Changes to Selected Data"),
                dbc.Button("Delete", id="delete", color="primary",
                           style={'display': 'inline-block', "margin": "5px"},
                           n_clicks=0),
                html.P("Move:"),
                dcc.Input(id="move", type="number", placeholder=""),
                dbc.Button("Make Changes", id="makeChanges", color="primary",
                           style={'display': 'inline-block', "margin": "5px"},
                           n_clicks=0),
                dbc.Button("Export Data", id="exportDF", color="primary",
                           style={'display': 'inline-block', "margin": "5px"},
                           n_clicks=0),
            ], body="true", color="light")
        ], width=2),
        dbc.Col(
            dbc.Card(
                dcc.Graph(id='indicator-graphic'), body='True', color="light"), width=10)
    ]),
    html.Hr(),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dcc.Markdown("""
                    **Click Data**

                    Click on a point from the graph to display more about that observation.
                """),
                html.Pre(id='selected'),
            ], body="true", color="light")
        ], width=2),
        dbc.Col([
            dbc.Card([html.Div(id="update-table"),
                      ], body="true", color="light")
        ], width=10)
    ])
])


@app.callback(
    Output('memory-output', 'data'),
    # Output('indicator-graphic', 'figure'),
    # Output('update-table', 'children'),
    Input('query', 'n_clicks'),
    State('site_id', 'value'))
def main_query(n_clicks, site_id):
    # Opening the database file
    print(f"button clicked {n_clicks} times")
    if db_name.endswith(".db"):
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()  # This object will allow queries to be ran on the database
    else:
        print("Cannot open database file")

    # SQL query on the database -- Depending on your database, this will need to be formatted
    # to fit your system requirements
    pressure_data = get_pressure(cursor, site_id)
    # discharge_data = get_discharge(cursor, site_id)

    table = pd.DataFrame(pressure_data)
    table['pressure_hobo'].replace('', np.nan, inplace=True)
    table.dropna(subset=['pressure_hobo'], inplace=True)
    table.drop('index', axis=1, inplace=True)

    figure = px.scatter(pressure_data, x=pressure_data.datetime, y=pressure_data.pressure_hobo,
                        color=pressure_data.batch_id)

    data = table.to_json()
    return data#, figure, html.Div(
    #     [
    #         dash_table.DataTable(
    #             data=table.to_dict("rows"),
    #             columns=[{"id": x, "name": x} for x in table.columns],
    #         )
    #     ]
    # )


@app.callback(
    Output('selected', 'children'),
    Input('indicator-graphic', 'clickData'))
def display_selected(clickData):
    return json.dumps(clickData, indent=1)


@app.callback(
    Output('update-table', 'children'),
    Input('indicator-graphic', 'selectedData'),
    State('memory-output', 'data'))
def display_selected_data(selectedData, data):
    pressure_table = pd.read_json(data)
    selected_styles = update_table_style(selectedData)
    return html.Div(
        [
            dash_table.DataTable(
                data=pressure_table.to_dict("rows"),
                columns=[{"id": x, "name": x} for x in pressure_table.columns],
                style_data_conditional=selected_styles,
            )
        ]
    )
def update_table_style(selectedData):
    if selectedData is not None:
        points_selected = []
        for point in selectedData['points']:
            points_selected.append(point['pointIndex'])
        selected_styles = [{'if': {'row_index': i},
                            'backgroundColor': 'pink'} for i in points_selected]

    return selected_styles

# deletes a point, updates the JSON and triggers refresh of graph's data.
@app.callback(
    Output("memory-output", "data"),
    Input("delete", "n_clicks"),
    State("indicator-graphic", "selectedData"),
    State("memory-output", 'data'))
def deletebutton(n_clicks, selection, data):
    df = pd.read_json(data)
    matched_points = []
    if selection is not None:
        datetimes_selected = []
        pressures_selected = []
        for point in selection['points']:
            datetimes_selected.append(point['x'])
            pressures_selected.append(point['y'])
        datetimes_series = df['datetime'].isin(datetimes_selected)
        matched_datetimes = df[datetimes_series]
        pressures_series = matched_datetimes['pressure_hobo'].isin(pressures_selected);
        matched_points = matched_datetimes[pressures_series]

    df.drop(matched_points.index, axis=0, inplace=True)

    return df.to_json()

@app.callback(
    Input("memory-output", "data"),
    Output('indicator-graphic', 'figure'),
    Output('update-table', 'children'))
def updateOnNewData(data):
    df = pd.read_json(data)
    figure = px.scatter(df, x=df.datetime, y=df.pressure_hobo,
                        color=df.batch_id)

    return figure, html.Div(
        [
            dash_table.DataTable(
                data=df.to_dict('rows'),
                columns=[{"id": x, "name": x} for x in df.columns],
            )
        ]
    )

if __name__ == '__main__':
    app.run_server(debug=True)


