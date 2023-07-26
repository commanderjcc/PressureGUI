import dash_bootstrap_components as dbc
from dash import Dash, dcc, html, dash_table

# Header contains the title and subtitle
header = [
    dbc.Row([
        dbc.Col(
            dbc.Card([
                html.H2("Abbott Lab GUI"),
                html.H5("Coolness overload")
            ], body="true", color="light"), width={"size": 10, "offset": 1})
    ]),
]

# Tabs containing the tabs for the main page

# Local storage is used to store data in the browser
localstorage = [
    dcc.Store(id='memory-output'),
    # dcc.Store(id='discharge'),
    # dcc.Store(id='selection-stats'),
    dcc.Store(id='history'),
    dcc.Store(id='updated-table'),
]

# Download is used to hold the dcc.Download components
download = [
    dcc.Download(id="download-csv"),
    dcc.Download(id="changes-csv")
]

# shift_tab is used to hold the shift controls
shift_tab = [
    html.P("Vertical Shift of:"),
    dcc.Input(id="shift_amount", type="number", placeholder="", style={'width': '100%'}),
    dbc.Button("Shift", id="shift_button", color="primary",
               style={'display': 'inline-block', "margin": "5px"},
               n_clicks=0),
]

# delete_tab is used to hold the delete button
delete_tab = [
    html.P("Delete Box or Lasso Selection"),
    dbc.Button("Delete", id="delete", color="primary",
               style={'display': 'inline-block', "margin": "5px"},
               n_clicks=0),
]

# compress_tab is used to hold the compression controls
compress_tab = [
    html.P("Compression factor:"),
    dcc.Input(id="compression_factor", type="number", placeholder="", style={'width': '100%'}),
    dbc.Button("Expand/Compress", id="compress_button", color="primary",
               style={'display': 'inline-block', "margin": "5px"},
               n_clicks=0),
]

# export_tab is used to hold the export controls
export_tab = [
    html.P("Export as CSV"),
    dcc.Input(id="export_filename", type="text", placeholder="export.csv", style={'width': '100%'}),
    dbc.Button("Export Data", id="exportDF", color="primary",
               style={'display': 'inline-block', "margin": "5px"},
               n_clicks=0),
]

# history_tab is used to hold the undo button
history_tab = [
    dbc.Button("Undo", id="undoChange", color="primary",
               style={'display': 'inline-block', "margin": "5px"},
               n_clicks=0),
    dbc.Accordion([], id="history_log", start_collapsed=True),
]

# editor is used to hold the tabs above for the editor
editor = [
    # dbc.Card([
    #     dbc.CardHeader([
    dbc.Accordion([
        dbc.AccordionItem(shift_tab, title="Shift︎"),
        dbc.AccordionItem(compress_tab, title="Compress"),
        dbc.AccordionItem(delete_tab, title="Delete"),
        dbc.AccordionItem(export_tab, title="Export"),
        dbc.AccordionItem(history_tab, title="History")
    ], start_collapsed=True),
    #     ]),
    #
    #     dbc.CardBody(id="editor_card_body")
    # ])
]

layout = dbc.Container([
    *localstorage,  # *localstorage expands the list into the container
    *download,
    *header,
    html.Hr(),
    dbc.Row([
        dbc.Col([
            dbc.Card([  # This is the card that holds the site query
                html.H5("Run Site Query"),
                "Site ID:",
                dcc.Dropdown(
                    options=['BEN', 'BLI', 'BSL', 'CLE', 'CRB', 'DAI', 'DFF', 'DFL', 'DFM', 'DFU', 'HCL',
                             'HCN', 'HCS', 'IND', 'LAK', 'LDF', 'MIT', 'NEB', 'PBC', 'SBL', 'SFL', 'SHE',
                             'SOL', 'STR', 'TCU', 'TIE', 'WAN'],
                    value='BEN',
                    id='site_id',
                    style={'display': 'inline-block', "width": "80%", "margin": "2px"}),
                dbc.Button("Query Site", id="query", color="primary",
                           style={'display': 'inline-block', "margin": "5px"},
                           n_clicks=0)
            ], body="true", color="light"),
            html.Hr(),
            *editor,  # *editor expands the editor components into the container
        ], width=3),
        dbc.Col(
            dbc.Card(
                dcc.Graph(id='indicator-graphic'), body='True', color="light"), width=9)  # This is the graph
    ]),
    html.Hr(),

    dbc.Row([
        dbc.Col([
            dbc.Card([  # This is the card that holds the mean and variance information
                dcc.Markdown("""
                    **Click Data**

                    Click on a point from the graph to display more about that observation.
                """),
                html.P("Selection Mean:"),
                html.P(id="mean"),
                html.P("Selection Variance:"),
                html.P(id="variance"),
            ], body="true", color="light")
        ], width=3),
        dbc.Col([
            dbc.Card([html.Div(id="update-table"),  # This is the card that holds the table
                      ], body="true", color="light")
        ], width=9)
    ])
])
