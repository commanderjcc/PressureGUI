# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, dcc, html, dash_table
from dash.dependencies import Output, Input, State
from dash_extensions.enrich import Output, DashProxy, Input, MultiplexerTransform
import dash_bootstrap_components as dbc

import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

import json
import numpy as np
import pandas as pd
from pathlib import Path
import statistics as stat

import sqlite3
from run_query import get_pressure, get_discharge
from layout import layout
from changes import apply_changes, log_changes, Change

# Declare the database file name here
db_name = "copy.db"

# app = Dash(external_stylesheets=[dbc.themes.FLATLY])
app = DashProxy(external_stylesheets=[dbc.themes.FLATLY],
                prevent_initial_callbacks=True, transforms=[MultiplexerTransform()])

app.layout = layout


@app.callback(
    Output('mean', 'children'),
    Output('variance', 'children'),
    Input('indicator-graphic', 'selectedData'))
def display_selected(selection):
    # print(selection)

    if selection is not None:
        pressures_selected = []
        for point in selection['points']:
            pressures_selected.append(point['y'])

        pressures_selected = pd.DataFrame(pressures_selected)

        return pressures_selected.mean(), pressures_selected.var()

    else:
        return 0, 0


@app.callback(
    Output('memory-output', 'data'),
    Output('discharge', 'data'),
    Output('history', 'data'),
    Input('query', 'n_clicks'),
    State('site_id', 'value'))
def main_query(n_clicks, site_id):
    # Opening the database file
    # print(f"button clicked {n_clicks} times")
    if db_name.endswith(".db"):
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()  # This object will allow queries to be run on the database
    else:
        print("Cannot open database file")

    # SQL query on the database -- Depending on your database, this will need to be formatted
    # to fit your system requirements
    pressure_data = get_pressure(cursor, site_id)

    table = pd.DataFrame(pressure_data)
    table['pressure_hobo'].replace('', np.nan, inplace=True)
    table.dropna(subset=['pressure_hobo'], inplace=True)
    table.drop('index', axis=1, inplace=True)

    discharge_data = get_discharge(cursor, site_id)
    discharge_df = pd.DataFrame(discharge_data)
    discharge_df['discharge_measured'].replace('', np.nan, inplace=True)
    discharge_df.dropna(subset=['discharge_measured'], inplace=True)
    discharge_df.drop('index', axis=1, inplace=True)

    data = table.to_json()
    discharge = discharge_df.to_json()
    change_log = log_changes([], "init", pd.DataFrame(), f"Initialized with site_id: {site_id}")
    return data, discharge, change_log


@app.callback(
    Output('update-table', 'children'),
    Input('indicator-graphic', 'selectedData'),
    State('memory-output', 'data'),
    State('updated-table', 'data')
)
def display_selected_data(selectedData, data, updatedData):
    pressure_table = pd.read_json(data)
    if selectedData is not None:
        selected_styles = update_table_style(selectedData)
        if updatedData is not None:
            pressure_table = pd.read_json(updatedData)
            return html.Div(
                [
                    dash_table.DataTable(
                        data=pressure_table.to_dict('rows'),
                        columns=[{'id': x, 'name': x} for x in pressure_table.columns],
                        style_data_conditional=selected_styles,
                    )
                ]
            )
        else:
            return html.Div(
                [
                    dash_table.DataTable(
                        data=pressure_table.to_dict('rows'),
                        columns=[{'id': x, 'name': x} for x in pressure_table.columns],
                        style_data_conditional=selected_styles,
                    )
                ]
            )
    else:
        pass


def update_table_style(selectedData):
    points_selected = []
    for point in selectedData['points']:
        points_selected.append(point['pointIndex'])
    selected_styles = [{'if': {'row_index': i},
                        'backgroundColor': 'pink'} for i in points_selected]

    return selected_styles


def dataframe_from_selection(data, selection):
    df = pd.read_json(data)

    if selection is not None:
        datetimes_selected = []
        pressures_selected = []
        # Add points from the selection
        for point in selection['points']:
            datetimes_selected.append(point['x'])
            pressures_selected.append(point['y'])
        # Search data for datetime matches
        datetimes_series = df['datetime'].isin(datetimes_selected)
        matched_datetimes = df[datetimes_series]
        # Search datetime matches for y-value matches
        pressures_series = matched_datetimes['pressure_hobo'].isin(pressures_selected);
        matched_points = matched_datetimes[pressures_series]

        return matched_points

@app.callback(
    Output('memory-output', 'data'),
    Output('history', 'data'),
    Input('shift_button', 'n_clicks'),
    State('memory-output', 'data'),
    State('history', 'data'),
    State('shift_amount', 'value'),
    State('indicator-graphic', 'selectedData')
)
def shift_selected_data(n_clicks, data, history, shift, selectedData):
    if n_clicks > 0 and shift is not None and selectedData is not None:
        data_df = pd.read_json(data)
        change_df = dataframe_from_selection(data, selectedData)

        if shift is not None:
            change_df['pressure_hobo'] = shift
            changed_df = apply_changes(data_df, change_df)

            start = change_df.iloc[0, 1]
            end = change_df.iloc[-1, 1]
            dir = "up" if (shift > 0) else "down"
            change_log = log_changes(history, "shift", change_df, f"shifted {dir} by {abs(shift)} from {start} to {end}")

            return changed_df.to_json(), change_log
    else:
        pass


@app.callback(
    Output('memory-output', 'data'),
    Output('history', 'data'),
    Input('compress_button', 'n_clicks'),
    State('memory-output', 'data'),
    State('history', 'data'),
    State('compression_factor', 'value'),
    State('indicator-graphic', 'selectedData')
)
def compress_selected_data(n_clicks, data, history, expcomp, selectedData):
    data_df = pd.read_json(data)
    if n_clicks > 0 and expcomp is not None and selectedData is not None:
        change_df = dataframe_from_selection(data, selectedData)

        if expcomp is not None:
            change_df_mean = stat.mean(change_df['pressure_hobo'])
            change_df['pressure_hobo'] = -(change_df['pressure_hobo'] - change_df_mean) / expcomp

            changed_df = apply_changes(data_df, change_df)

            start = change_df.iloc[0, 1]
            end = change_df.iloc[-1, 1]
            change_log = log_changes(history, "compression", change_df, f"compressed by factor of {expcomp} around the mean of {change_df_mean} from {start} to {end}")

            return changed_df.to_json(), change_log
    else:
        pass


@app.callback(
    Output('memory-output', 'data'),
    Output('history', 'data'),
    Input('delete', 'n_clicks'),
    State('indicator-graphic', 'selectedData'),
    State('memory-output', 'data'),
    State('history', 'data')
)
def delete_button(n_clicks, selection, data, history):
    # Read in dataframe from local JSON store.
    df = pd.read_json(data)

    if selection is not None:
        change_df = dataframe_from_selection(data, selection)

        # remove the data points from the data frame
        df.drop(change_df.index, axis=0, inplace=True)  # TODO what does inplace do?

        start = change_df.iloc[0, 1]
        end = change_df.iloc[-1, 1]
        change_log = log_changes(history, "delete", change_df, f"deleted {change_df.shape[0]} points from {start} to {end}")

        # Save the data into the Local json store and trigger the graph update.
        return df.to_json(), change_log
    else:
        pass


@app.callback(
    Input('memory-output', 'data'),
    State('discharge', 'data'),
    Output('indicator-graphic', 'figure'),
    Output('update-table', 'children'))
def update_on_new_data(data, discharge):
    # Read in dataframe from JSON
    df = pd.read_json(data)
    discharge = pd.read_json(discharge)
    # Convert batch_id to strings
    df['batch_id'] = df['batch_id'].apply(lambda x: str(x))
    discharge['batch_id'] = df['batch_id'].apply(lambda x: str(x))

    # Create a scatterplot figure from the dataframe
    # figure = px.scatter(df, x=df.datetime, y=df.pressure_hobo,
    #                     color=df.batch_id)

    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add traces
    fig.add_trace(
        go.Scatter(x=df.datetime, y=df.pressure_hobo,  # replace with your own data source
                   name="pressure", mode='markers'),
        secondary_y=False
    )

    fig.add_trace(
        go.Scatter(x=discharge.datetime, y=discharge.discharge_measured, name="discharge", mode="lines+markers"),
        secondary_y=True,
    )


    # create a DashTable from the data
    table = html.Div(
        [
            dash_table.DataTable(
                data=df.to_dict('rows'),
                columns=[{'id': x, 'name': x} for x in df.columns],
            )
        ]
    )

    # return objects into the graph and table
    return fig, table

@app.callback(
    Input('history', 'data'),
    Output('history_log', 'children')
)
def display_changelog(history):
    children = []
    if (isinstance(history,str)):
        try:
            history = json.loads(history)
        except:
            print("ERROR: couldn't parse json history string, save your work and run while you still can")
    for change in history:
        change = Change(change)
        children.append(
            dbc.AccordionItem([
                change.description
            ], title=change.type)
        )

    return children


@app.callback(
    Input('undoChange', 'n_clicks'),
    State('history', 'data'),
    State('memory-output', 'data'),
    Output('memory-output', 'data'),
    Output('history', 'data')
)
def undo(n_clicks, history, data):
    # if already initialized
    if len(history) > 1:
        change = Change(history.pop())
        data = change.undoFunc(data, change.changes_df)
        return data.to_json(), history
    else:
        pass

@app.callback(
    Output('download-csv', 'data'),
    Output('changes-csv', 'data'),
    Input('exportDF', 'n_clicks'),
    State('memory-output', 'data'),
    State('history', 'data'),
    State('export_filename', 'value'),
    prevent_initial_call=True
)
def export(n_clicks, data, changes, filename):
    if data is not None:
        pressure_table = pd.read_json(data)
        changestr = json.dumps(changes)
        return dcc.send_data_frame(pressure_table.to_csv, filename), dict(content=changestr, filename="changes.json")


if __name__ == '__main__':
    app.run_server(debug=True)
