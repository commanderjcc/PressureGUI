# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

# Throughout the code, there are commented lines that can be uncommented to enable discharge graphing,
# this comes at a significant performance cost and will require other modifications.
# So it's left as an exercise for the reader ;)  *(you can check out the github commit history for a hint)*

# Import dash modules
from dash import Dash, dcc, html, dash_table
from dash.dependencies import Output, Input, State
from dash_extensions.enrich import Output, DashProxy, Input, MultiplexerTransform
import dash_bootstrap_components as dbc

# Import plotly modules
import plotly.express as px
# from plotly.subplots import make_subplots
# import plotly.graph_objects as go

# Import data modules
import json
import numpy as np
import pandas as pd
from pathlib import Path
import statistics as stat
import sqlite3

# Import custom modules
from run_query import get_pressure, get_discharge
from layout import layout
from changes import apply_changes, log_changes, Change

# Declare the database file name here
db_name = "copy.db"

# app = Dash(external_stylesheets=[dbc.themes.FLATLY])
app = DashProxy(external_stylesheets=[dbc.themes.FLATLY],
                prevent_initial_callbacks=True, transforms=[MultiplexerTransform()])

# layout is stored in the layout.py file
app.layout = layout


@app.callback(
    Output('mean', 'children'),
    Output('variance', 'children'),
    Input('indicator-graphic', 'selectedData'))
def display_selected(selection):
    """
        This function is called when the user selects a region on the graph. It will display the mean and variance
    """

    if selection is not None:
        pressures_selected = []
        for point in selection['points']:
            pressures_selected.append(point['y'])  # the y value is the pressure, append all to a list

        pressures_selected = pd.DataFrame(pressures_selected)  # convert to a dataframe for easy statistics

        return pressures_selected.mean(), pressures_selected.var()  # return the mean and variance

    else:
        return 0, 0


@app.callback(
    Output('memory-output', 'data'),
    # Output('discharge', 'data'),
    Output('history', 'data'),
    Input('query', 'n_clicks'),
    State('site_id', 'value'))
def main_query(n_clicks, site_id):
    """
        This function is called when the user clicks the "Query" button. It will query the database and return the data
        for the selected site_id. This data is stored in the local storage of the browser, and triggers an update to the
        graph and table through the stores's callbacks.
    """
    try:
        assert db_name.endswith(".db")
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()  # This object will allow queries to be run on the database
    except sqlite3.Error as e:
        print("Cannot open database file")

    # SQL query on the database -- Depending on your database, this will need to be formatted
    # to fit your system requirements
    pressure_data = get_pressure(cursor, site_id)

    table = pd.DataFrame(pressure_data)  # make sure the data is in a dataframe
    table['pressure_hobo'].replace('', np.nan, inplace=True)  # replace empty values with NaN
    table.dropna(subset=['pressure_hobo'], inplace=True)  # drop rows with NaN values
    table.drop('index', axis=1, inplace=True)  # drop the index column  # TODO probably not necessary, but it's here

    # discharge_data = get_discharge(cursor, site_id)
    # discharge_df = pd.DataFrame(discharge_data)
    # discharge_df['discharge_measured'].replace('', np.nan, inplace=True)
    # discharge_df.dropna(subset=['discharge_measured'], inplace=True)
    # discharge_df.drop('index', axis=1, inplace=True)

    data = table.to_json()  # convert the dataframe to json for storage in the browser
    # discharge = discharge_df.to_json()

    # initialize the change log for undo functionality
    change_log = log_changes([], "init", pd.DataFrame(), f"Initialized with site_id: {site_id}")
    return data, change_log


@app.callback(
    Output('update-table', 'children'),
    Input('indicator-graphic', 'selectedData'),
    State('memory-output', 'data'),
    State('updated-table', 'data')
)
def display_selected_data(selectedData, data, updatedData):
    """
        This function is called when the user selects a region on the graph. It will display the selected data in a
        table below the graph.
    """

    pressure_table = pd.read_json(data)  # read the data from the local storage
    if selectedData is not None:
        selected_styles = update_table_style(selectedData)  # update the styling of the table based on the selection
        if updatedData is not None:
            pressure_table = pd.read_json(updatedData)  # used the updated data if it exists  # TODO this is a bit jank
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
    """
        This function is called when the user selects a region on the graph. It will update the styling of the table
        based on the selection. There's proabably a better way to do this, but it works for now.
    """

    points_selected = []
    for point in selectedData['points']:
        points_selected.append(point['pointIndex'])
    selected_styles = [{'if': {'row_index': i},
                        'backgroundColor': 'pink'} for i in points_selected]  # make the selected rows pink

    return selected_styles


def dataframe_from_selection(data, selection):
    """
        Returns a dataframe that contains only the points selected on the graph.
    :param data: A JSON string containing the data from the local storage
    :param selection: A dictionary from the selectedData property of the graph
    :return:
    """
    df = pd.read_json(data)  # read the data from the local storage

    if selection is not None:
        datetimes_selected = []  # initialize empty lists, datetimes are the x-values
        pressures_selected = []  # pressures are the y-values
        # Add points from the selection
        for point in selection['points']:
            datetimes_selected.append(point['x'])
            pressures_selected.append(point['y'])
        # Search data for datetime matches
        datetimes_series = df['datetime'].isin(datetimes_selected)  # returns a boolean series
        matched_datetimes = df[datetimes_series]  # returns a dataframe of only the matched datetimes
        # Search datetime matches for y-value matches
        pressures_series = matched_datetimes['pressure_hobo'].isin(pressures_selected)  # returns a boolean series
        matched_points = matched_datetimes[pressures_series]  # returns a dataframe of only the matched pressures

        return matched_points  # return the dataframe of points that matched both x and y


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
    """
        This function is called when the user clicks the shift button. It will shift the selected data by the amount
        specified in the shift_amount input box. It will also update the change log.

    :param n_clicks: used to determine if the button has been clicked
    :param data: local storage of the pressure data
    :param history: local storage of the change log
    :param shift: the amount to shift the data by
    :param selectedData: the currently selected data
    :return: the updated data and change log
    """
    if n_clicks > 0 and shift is not None and selectedData is not None:
        data_df = pd.read_json(data)  # read the data from the local storage
        change_df = dataframe_from_selection(data, selectedData)  # get the selected data as a dataframe

        if shift is not None:
            change_df['pressure_hobo'] = shift  # set the pressure column to the shift amount
            changed_df = apply_changes(data_df, change_df)  # apply the changes to the data

            start = change_df.iloc[0, 1]  # get the start and end values for the change log
            end = change_df.iloc[-1, 1]

            dir = "up" if (shift > 0) else "down"  # determine if the shift was up or down
            change_log = log_changes(history, "shift", change_df,
                                     f"shifted {dir} by {abs(shift)} from {start} to {end}")

            return changed_df.to_json(), change_log  # return the updated data and change log
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
    """
        This function is called when the user clicks the compress button. It will compress the selected data by the
        amount specified in the compression_factor input box. It will also update the change log.

    :param n_clicks:  used to determine if the button has been clicked
    :param data:  local storage of the pressure data
    :param history:  local storage of the change log
    :param expcomp:  the amount to expand/compress the data by
    :param selectedData:  the currently selected data
    :return:  the updated data and change log
    """
    data_df = pd.read_json(data)  # read the data from the local storage
    if n_clicks > 0 and expcomp is not None and selectedData is not None:
        change_df = dataframe_from_selection(data, selectedData)  # get the selected data as a dataframe

        if expcomp is not None:
            change_df_mean = stat.mean(change_df['pressure_hobo'])  # get the mean of the selected data

            #  shift down by the expansion/compression factor multiplied by the height above the mean (whew, confusing)
            change_df['pressure_hobo'] = -(change_df['pressure_hobo'] - change_df_mean) / expcomp

            changed_df = apply_changes(data_df, change_df)  # apply the changes to the data

            start = change_df.iloc[0, 1]  # get the start and end values for the change log
            end = change_df.iloc[-1, 1]
            change_log = log_changes(history, "compression", change_df,
                                     f"compressed by factor of {expcomp} around the mean of {change_df_mean} from {start} to {end}")

            return changed_df.to_json(), change_log  # return the updated data and change log
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
    """
        This function is called when the user clicks the delete button. It will delete the selected data from the
        graph and update the change log.

    :param n_clicks:  used to determine if the button has been clicked
    :param selection:  the currently selected data
    :param data:  local storage of the pressure data
    :param history: local storage of the change log
    :return:  the updated data and change log
    """

    # Read in dataframe from local JSON store.
    df = pd.read_json(data)

    if selection is not None:
        change_df = dataframe_from_selection(data, selection)  # get the selected data as a dataframe

        # remove the data points from the data frame
        df.drop(change_df.index, axis=0, inplace=True)

        start = change_df.iloc[0, 1]  # get the start and end values for the change log
        end = change_df.iloc[-1, 1]
        change_log = log_changes(history, "delete", change_df,
                                 f"deleted {change_df.shape[0]} points from {start} to {end}")

        # Save the data into the Local json store and trigger the graph update.
        return df.to_json(), change_log
    else:
        pass


@app.callback(
    Input('memory-output', 'data'),
    # State('discharge', 'data'),
    Output('indicator-graphic', 'figure'),
    Output('update-table', 'children'))
def update_on_new_data(data):
    """
        This function is called when the data is updated. It will update the graph and the table.

    :param data: local storage of the pressure data
    :return: the updated graph and table
    """

    # Read in dataframe from JSON
    df = pd.read_json(data)

    # discharge = pd.read_json(discharge)

    # Convert batch_id to strings
    df['batch_id'] = df['batch_id'].apply(lambda x: str(x))  # TODO theres a better way to do this

    # discharge['batch_id'] = df['batch_id'].apply(lambda x: str(x))

    # Create a scatterplot figure from the dataframe with discharge data
    # figure = px.scatter(df, x=df.datetime, y=df.pressure_hobo,
    #                     color=df.batch_id)

    # Create figure with secondary y-axis
    # fig = make_subplots(specs=[[{"secondary_y": True}]])
    #
    # # Add traces
    # fig.add_trace(
    #     go.Scatter(x=df.datetime, y=df.pressure_hobo,  # replace with your own data source
    #                name="pressure", mode='markers'),
    #     secondary_y=False
    # )
    #
    # fig.add_trace(
    #     go.Scatter(x=discharge.datetime, y=discharge.discharge_measured, name="discharge", mode="lines+markers"),
    #     secondary_y=True,
    # )

    fig = px.scatter(df, x=df.datetime, y=df.pressure_hobo, color=df.batch_id)  # create a scatterplot figure

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
    """
        This function is called when the change log is updated. It will update the change log display.
    :param history:  local storage of the change log
    :return:  the updated change log display
    """

    children = []
    if (isinstance(history, str)):  # if the history is a string, its probably JSON
        try:
            history = json.loads(history)  # parse the json string
        except:
            print("ERROR: couldn't parse json history string, save your work and run while you still can")
    for change in history:
        change = Change(change)  # create a change object from the dictionary
        children.append(
            dbc.AccordionItem([
                change.description  # add the description to the accordion item
            ], title=change.type)  # add the type to the accordion title
        )

    return children  # return the change log display


@app.callback(
    Input('undoChange', 'n_clicks'),
    State('history', 'data'),
    State('memory-output', 'data'),
    Output('memory-output', 'data'),
    Output('history', 'data')
)
def undo(n_clicks, history, data):
    """
        This function is called when the user clicks the undo button. It will undo the last change and update the
        change log.

    :param n_clicks: used to determine if the button has been clicked
    :param history:  local storage of the change log
    :param data:  local storage of the pressure data
    :return:  the updated data and change log
    """
    # if already initialized
    if len(history) > 1:  # there has to be at least one change to undo and one to fall back on
        change = Change(history.pop())  # get the last change from the history
        data = change.undoFunc(data, change.changes_df)  # undo the change
        return data.to_json(), history  # return the updated data and change log
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
    """
        This function is called when the user clicks the export button. It will export the data to CSV and the change
        log to a JSON file.
    :param n_clicks:  used to determine if the button has been clicked
    :param data:  local storage of the pressure data
    :param changes:  local storage of the change log
    :param filename:  the name of the file to export to
    :return:  a CSV file of the data and a JSON file of the change log
    """

    if data is not None:
        pressure_table = pd.read_json(data)  # read in the data from the local storage
        changestr = json.dumps(changes)  # convert the change log to a string

        # return the data as a CSV file and the change log as a JSON file to the dcc.Download component
        return dcc.send_data_frame(pressure_table.to_csv, f"{filename}.csv"), \
               dict(content=changestr, filename=f"{filename}.json")


if __name__ == '__main__':
    app.run_server(debug=True)
