"""
Main dash application.
"""
from dash import Dash, html, dcc, callback, Output, Input, dash_table
import dash_daq as daq
import dash_bootstrap_components as dbc
from plotly.graph_objects import Figure
import pandas as pd
from typing import List, Dict, Any
import configparser
from src.data_loading import URLBuilder, WebcommandDataLoader, DataFormatter
from src.plotting import TimeseriesPlotter, HistogramPlotter, HeatmapPlotter
from src.utils import COLUMN, Logging, HEATMAP_VALUE, filter_by_date
import os

config = configparser.ConfigParser()
config.read("src/config.ini")

Logging.setup()
logger = Logging.get_console_logger()

logger.info("App starting - here we go.")

PORT = os.environ["PORT"]
TOKEN = os.environ["TOKEN"]
url_builder = URLBuilder(TOKEN)
data_loader = WebcommandDataLoader(url_builder)
data_formatter = DataFormatter()

# get device IDs
unique_ids = data_loader.load_device_ids()
unique_ids = data_formatter.process_records_to_dataframe(unique_ids)
unique_ids = unique_ids[COLUMN.DEVICEID]

app = Dash(
    "Noise-App",
    title="NoisePressureMonitor",
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)
server = app.server


card = dbc.Card(
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


def get_intro_markdown():
    """
    Intro text after the title.
    """
    text = """
            Environmental noise, especially in urban settings, is a [known public health concern](https://www.toronto.ca/wp-content/uploads/2017/11/8f98-tph-How-Loud-is-Too-Loud-Health-Impacts-Environmental-Noise.pdf):
            >
            > _"The growing body of evidence indicates that exposure to excessive environmental noise does not only impact quality of life and cause hearing loss but also has other health impacts, such as cardiovascular effects, cognitive impacts, sleep disturbance and mental health effects."_
            >
            Our application presents a real-time, interactive visual interface to a system of IoT sound meters deployed in the city of Toronto, Ontario, to better understand the ambient sound levels as well as extreme noise events local communities experience day to day.
            Start by selecting a device from the drop-down.
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
            style={"margin-left": "30px", "margin-right": "150px"},
        ),
        html.Br(),
        dbc.Row(
            [
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
                            unique_ids, unique_ids[0], id="id-selection"
                        ),
                    ],
                    width={"offset": 2},
                )
            ],
            style=dict(width="33.33%"),
        ),
        dbc.Row(dbc.Spinner(dcc.Graph(id="noise-level-line"))),
        dbc.Row(
            [dcc.Markdown(id="middle-markdown")],
            style={"margin-left": "30px", "margin-right": "150px"},
        ),
        dbc.Row(
            [
                dbc.Col(dbc.Spinner(dcc.Graph(id="heatmap")), width=9),
                dbc.Col(
                    [
                        html.Br(),
                        html.Br(),
                        card,
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
                dbc.Col(dbc.Spinner(dcc.Graph(id="histogram"))),
            ],
            align="center",
        ),
    ],
    fluid=True,
    style={"backgroundColor": config["app.colors"]["background"]},
)


#################
### CALLBACKS ###
#################

# CARD CALLBACKS


@callback(Output("card-text", "children"), Input("device-stats", "data"))
def update_card_text(stats: List[dict]) -> str:
    """
    Insert device id into the card.
    """
    stats_dict = stats[0]

    count = stats_dict[COLUMN.COUNT.value]

    date_format = "%Y-%m-%d"
    min_date = stats_dict[COLUMN.MINDATE.value]
    formatted_min_date = pd.to_datetime(min_date).strftime(date_format)

    max_date = stats_dict[COLUMN.MAXDATE.value]
    formatted_max_date = pd.to_datetime(max_date).strftime(date_format)

    max_noise = stats_dict[COLUMN.MAXNOISE.value]

    text = (
        f"This device has recorder a total of {count} measurements between "
        f" {formatted_min_date} and {formatted_max_date}. "
        f" The loudest measurement recorded to date was at {max_noise} dBA."
    )

    return text


@callback(Output("card-header", "children"), Input("id-selection", "value"))
def update_card_header(device_id: str) -> str:
    """
    Insert device id into the card.
    """

    return f"Device ID: {device_id}"


@callback(
    Output("middle-markdown", "children"), Input("id-selection", "value")
)
def update_middle_markdown(device_id: str) -> str:
    """
    Add the text explaining what is on the line chart and how to use the heatmap.
    """
    return f"The plot shows measurements recorded by the device {device_id}, sent at 5 minute intervals. To select a different week to show click the heatmap below."


# DATA CALLBACKS


@callback(Output("device-stats", "data"), Input("id-selection", "value"))
def load_device_stats(device_id: str) -> List[Dict[str, Any]]:
    """
    Load the data from the API.
    """
    raw_stats = data_loader.load_device_stats(device_id=device_id)

    return raw_stats


@callback(Output("hourly-device-data", "data"), Input("id-selection", "value"))
def load_hourly_data(device_id: str) -> List[Dict[str, Any]]:
    """
    Load the data from the API.
    """
    raw_hourly_data = data_loader.load_hourly_data(device_id=device_id)

    return raw_hourly_data


@callback(
    Output("device-data", "data"),
    Input("id-selection", "value"),
    Input("device-stats", "data"),
    Input("heatmap", "clickData"),
)
def load_data(
    device_id: str, stats: List[dict], clickData: Dict
) -> List[Dict[str, Any]]:
    """
    Load the data from the API.
    """

    date_format = "%Y-%m-%d"
    if clickData:
        # user selects end date
        date_string = clickData["points"][0]["x"]
        end_date = pd.Timestamp(date_string).strftime(date_format)

    else:
        # last recorded date used as end
        stats_dict = stats[0]
        end_date = stats_dict[COLUMN.MAXDATE.value]
        end_date = pd.to_datetime(end_date).strftime(date_format)

    # look back 7 days
    start_date = pd.to_datetime(end_date) - pd.Timedelta(days=7)
    start_date = start_date.strftime(date_format)

    # load data from API
    raw_device_data = data_loader.load_noise_data(
        device_id=device_id, end_date=end_date, start_date=start_date
    )

    return raw_device_data


# PLOT CALLBACKS


@callback(
    Output("noise-level-line", "figure"),
    Input("device-data", "data"),
    Input("id-selection", "value"),
)
def update_noise_level_fig(
    data: List[Dict[str, Any]], device_id: str
) -> Figure:
    """
    Filter the line for a single device id.
    """
    df = data_formatter.process_records_to_dataframe(data)

    timeseries_plotter = TimeseriesPlotter(df)

    return timeseries_plotter.plot()


@callback(
    Output("histogram", "figure"),
    Input("device-data", "data"),
)
def update_histogram(data: List[Dict[str, Any]]) -> Figure:
    """
    Histogram of min/max distribution.
    """
    df = data_formatter.process_records_to_dataframe(data)

    hist_plotter = HistogramPlotter(df)

    return hist_plotter.plot()


@callback(
    Output("heatmap", "figure"),
    Input("hourly-device-data", "data"),
    Input("heatmap-toggle", "value"),
)
def update_heatmap(data: List[Dict[str, Any]], max_toggle: bool) -> Figure:
    df = data_formatter.process_records_to_dataframe(data)
    heatmap_plotter = HeatmapPlotter(df)

    if max_toggle:
        title = "Hourly Highest Measures - click to filter for the week!"
        pivot_value = HEATMAP_VALUE.MAX
    else:
        title = "Hourly Ambient Noise - click to filter for the week!"
        pivot_value = HEATMAP_VALUE.MIN

    return heatmap_plotter.plot(pivot_value=pivot_value, title=title)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=PORT)
