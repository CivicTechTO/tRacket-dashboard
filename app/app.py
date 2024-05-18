"""
Main dash application.
"""
from dash import Dash, html
import dash
import dash_bootstrap_components as dbc
import configparser
from src.utils import Logging, dbc_themes_name_to_url
import os

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
    "tRacket Dashboard",
    title="tRacket Dashboard",
    external_stylesheets=[theme_url, dbc.icons.FONT_AWESOME],
    use_pages=True,
)
server = app.server

app.layout = html.Div([dash.page_container])

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=PORT)
