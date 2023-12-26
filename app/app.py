"""
Main dash application.
"""
from dash import Dash, html, dcc
import dash_daq as daq
import dash_bootstrap_components as dbc

import configparser
from src.data_loading import URLBuilder, WebcommandDataLoader, AppDataManager
from src.app_callbacks_components import CallbackManager, GraphManager
from src.utils import Logging
import os

### Configs & Settings ###

config = configparser.ConfigParser()
config.read("src/config.ini")

PORT = os.environ["PORT"]
TOKEN = os.environ["TOKEN"]


### Setup Logging ###

Logging.setup()
logger = Logging.get_console_logger()
logger.info("App starting - here we go.")


### Setup Data Loader & Data Manager ###

# data loader - this could be swapped for local testing in the future
url_builder = URLBuilder(TOKEN)
data_loader = WebcommandDataLoader(url_builder)

# data manager
app_data_manager = AppDataManager(data_loader)

# load data
app_data_manager.load_data()


### Setup App ###

app = Dash(
    "Noise-App",
    title="Noise Pressure Monitor",
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)
server = app.server

# setup callbacks

CallbackManager.initialize_callbacks(app_data_manager)


### Setup Components ###

GraphManager.initialize_components(app_data_manager)

summary_card = dbc.Card(
    [
        dbc.CardHeader(id="card-header"),
        dbc.CardBody(
            [
                html.H4("Summary", className="card-title"),
                html.P(
                    id="card-text",
                    className="card-text",
                ),
            ]
        ),
    ],
    style={"width": "18rem"},
)


def get_intro_markdown() -> dcc.Markdown:
    """
    Intro text after the title.
    """
    text = """
            Environmental noise, especially in urban settings, is a [known public health concern](https://www.toronto.ca/wp-content/uploads/2017/11/8f98-tph-How-Loud-is-Too-Loud-Health-Impacts-Environmental-Noise.pdf):
            >
            > _"The growing body of evidence indicates that exposure to excessive environmental noise does not only impact quality of life and cause hearing loss but also has other health impacts, such as cardiovascular effects, cognitive impacts, sleep disturbance and mental health effects."_
            >
            Our application presents a real-time, interactive visual interface to a system of IoT sound meters deployed in the city of Toronto, Ontario, to better understand the ambient sound levels as well as extreme noise events local communities experience day to day.
            """

    return dcc.Markdown(text)


app.layout = dbc.Container(
    [
        html.Div([dcc.Store(id="device-data")]),
        html.Div([dcc.Store(id="device-stats")]),
        html.Div([dcc.Store(id="hourly-device-data")]),
        html.Br(),
        html.H1(
            children="🎧 Noise Pressure Monitor 🎧",
            style={"textAlign": "left", "margin-left": "30px"},
        ),
        html.Br(),
        dbc.Row(
            [get_intro_markdown()],
            style={
                "margin-left": "30px",
            },
        ),
        html.Br(),
        dbc.Row(
            [
                html.H2(
                    children="System Statistics",
                    style={"textAlign": "left", "margin-left": "30px"},
                ),
                dcc.Markdown(
                    "The summary statistics are calculated by aggregating data for the past 7 days and comparing to the prior week.",
                    style={"textAlign": "left", "margin-left": "30px"},
                ),
                dbc.Col([dbc.Spinner(GraphManager.system_count_indicator)]),
                dbc.Col([dbc.Spinner(GraphManager.system_avg_indicator)]),
                dbc.Col([dbc.Spinner(GraphManager.system_outlier_indicator)]),
            ],
            align="start",
        ),
        dbc.Row(
            [
                html.H2(
                    children="Device Monitor",
                    style={"textAlign": "left", "margin-left": "30px"},
                ),
                html.Br(),
                dcc.Markdown(
                    "Start by selecting a device from the drop-down.",
                    style={"textAlign": "left", "margin-left": "30px"},
                ),
                html.Br(),
                dbc.Col(
                    [
                        html.Label(
                            ["Select a Device:"],
                            style={
                                "font-weight": "bold",
                                "text-align": "left",
                            },
                        ),
                        dcc.Dropdown(
                            app_data_manager.unique_ids,
                            app_data_manager.unique_ids[0],
                            id="id-selection",
                        ),
                    ],
                    width={"offset": 2},
                ),
            ],
            style=dict(width="33.33%"),
        ),
        dbc.Row(dbc.Spinner(GraphManager.noise_line_graph)),
        dbc.Row(
            [dcc.Markdown(id="middle-markdown")],
            style={"margin-left": "30px", "margin-right": "150px"},
        ),
        dbc.Row(
            [
                dbc.Col(dbc.Spinner(GraphManager.heatmap), width=9),
                dbc.Col(
                    [
                        html.Br(),
                        html.Br(),
                        summary_card,
                        html.Br(),
                        daq.ToggleSwitch(
                            id="heatmap-toggle",
                            vertical=False,
                            label="Toggle Heatmap Min/Max",
                        ),
                    ],
                    width=3,
                    align="start",
                ),
            ],
            align="center",
        ),
        dbc.Row(
            [
                dbc.Col(dbc.Spinner(GraphManager.histogram)),
            ],
            align="center",
        ),
    ],
    fluid=True,
    style={"backgroundColor": config["app.colors"]["background"]},
)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=PORT)
