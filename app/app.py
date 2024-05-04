"""
Main dash application.
"""
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
import configparser
from src.utils import Logging, dbc_themes_name_to_url
import os
from src.data_loading.main import get_locations, create_api


### Configs & Settings ###

config = configparser.ConfigParser()
config.read("src/config.ini")

# get secrets
PORT = os.environ["PORT"]
TOKEN = os.environ["TOKEN"]

### Setup Logging ###

Logging.setup()
logger = Logging.get_console_logger()
logger.info("App starting - here we go.")


# get theme
theme_name = config["bootstrap"]["theme"]
theme_url = dbc_themes_name_to_url[theme_name]


### Setup App ###


app = Dash(
    "Noise-App",
    title="Noise Pressure Monitor",
    external_stylesheets=[theme_url, dbc.icons.FONT_AWESOME],
)
server = app.server

### Data loading ###

api = create_api()
locations = get_locations(api)

app.layout = dbc.Container([html.Div("text")])


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=PORT)


# ### Setup Data Loader & Data Manager ###

# # data loader - this could be swapped for local runtime in the future
# url_builder = URLBuilder(TOKEN)
# data_loader = WebcommandDataLoader(url_builder)

# # data manager
# app_data_manager = AppDataManager(data_loader)

# # load data
# app_data_manager.load_data()


# app = Dash(
#     "Noise-App",
#     title="Noise Pressure Monitor",
#     external_stylesheets=[theme_url, dbc.icons.FONT_AWESOME],
# )
# server = app.server

# ### Setup Components & Callbacks ###

# GraphManager.initialize(app_data_manager)
# InputManager.initialize(app_data_manager)
# CallbackManager.initialize(app_data_manager)
# MarkdownManager.initialize(app_data_manager)
# DataStoreManager.initialize()


# ### Layout ###

# app.layout = dbc.Container(
#     [
#         html.Div([DataStoreManager.device_data_store]),
#         html.Div([DataStoreManager.device_stats_store]),
#         html.Div([DataStoreManager.hourly_device_data_store]),
#         html.Div([MarkdownManager.navbar]),
#         html.Br(),
#         html.Br(),
#         html.Br(),
#         html.Br(),
#         html.H2(
#             children="Week in Numbers ",
#             style={"textAlign": "center"},
#         ),
#         dbc.Row([GraphManager.system_map]),
#         dbc.Row(
#             [
#                 dbc.Col([GraphManager.system_count_indicator]),
#                 dbc.Col([GraphManager.system_avg_indicator]),
#                 dbc.Col([GraphManager.system_outlier_indicator]),
#             ],
#             align="start",
#         ),
#         html.Br(),
#         html.Br(),
#         dbc.Row(
#             [
#                 dbc.Col(
#                     [MarkdownManager.device_card],
#                     # width={"size": 8, "offset": 2},
#                 ),
#                 dbc.Col([GraphManager.device_map]),
#             ],
#         ),
#         dbc.Row(
#             [
#                 dbc.Col(GraphManager.day_time_indicator),
#                 dbc.Col(GraphManager.evening_time_indicator),
#                 dbc.Col(GraphManager.night_time_indicator),
#             ]
#         ),
#         html.Br(),
#         html.Br(),
#         dbc.Tabs(
#             [
#                 dbc.Tab(
#                     [dbc.Spinner(GraphManager.noise_line_graph)],
#                     label="Measurements",
#                 ),
#                 dbc.Tab(
#                     [dbc.Spinner(GraphManager.histogram)],
#                     label="More Stats",
#                 ),
#             ]
#         ),
#         dbc.Row(
#             [
#                 dbc.Stack(
#                     [
#                         dbc.Col(
#                             [InputManager.heatmap_toggle], width={"offset": 1}
#                         ),
#                         dbc.Spinner(GraphManager.heatmap),
#                     ],
#                     gap=0,
#                 )
#             ],
#             align="center",
#         ),
#     ],
#     fluid=True,
# )
