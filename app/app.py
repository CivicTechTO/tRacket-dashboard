"""
Main dash application.
"""
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
import configparser
from src.data_loading import URLBuilder, WebcommandDataLoader, AppDataManager
from src.app_components import (
    CallbackManager,
    GraphManager,
    InputManager,
    MarkdownManager,
    DataStoreManager,
)
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

# data loader - this could be swapped for local runtime in the future
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

### Setup Components & Callbacks ###

GraphManager.initialize(app_data_manager)
InputManager.initialize(app_data_manager)
CallbackManager.initialize(app_data_manager)
MarkdownManager.initialize(app_data_manager)
DataStoreManager.initialize()


app.layout = dbc.Container(
    [
        html.Div([DataStoreManager.device_data_store]),
        html.Div([DataStoreManager.device_stats_store]),
        html.Div([DataStoreManager.hourly_device_data_store]),
        html.Br(),
        html.H1(
            children="🎧 Noise Pressure Monitor 🎧",
            style={"textAlign": "left", "margin-left": "30px"},
        ),
        html.Br(),
        dbc.Row([MarkdownManager.intro_markdown]),
        html.Br(),
        dbc.Row(
            [
                html.H2(
                    children="System Statistics",
                    style={"textAlign": "left", "margin-left": "30px"},
                ),
                MarkdownManager.system_stats_markdown,
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
                        InputManager.device_id_dropdown,
                    ],
                    width={"offset": 2},
                ),
            ],
            style=dict(width="33.33%"),
        ),
        dbc.Row(dbc.Spinner(GraphManager.noise_line_graph)),
        dbc.Row(
            [MarkdownManager.heatmap_markdown],
        ),
        dbc.Row(
            [
                dbc.Col(dbc.Spinner(GraphManager.heatmap), width=9),
                dbc.Col(
                    [
                        html.Br(),
                        html.Br(),
                        MarkdownManager.summary_card,
                        html.Br(),
                        InputManager.heatmap_toggle,
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
