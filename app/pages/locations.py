"""
The main map page of the application.
"""

import dash
from dash import html
import dash_bootstrap_components as dbc
from src.data_loading.main import get_locations, create_api, AppDataManager
from src.utils import DataFormatter, load_config
from src.app_components import LeafletMapComponentManager, COMPONENT_ID, GraphManager
from src.plotting import TimeseriesPlotter, MeanIndicatorPlotter
from dash import callback, Input, Output, dcc, html, State

config = load_config()


### Data loading ###

data_manager = AppDataManager()
data_manager.load_and_format_locations()

# map string col names to enum
dataformatter = DataFormatter()
locations = dataformatter._string_col_names_to_enum(data_manager.locations)


### Dash Page Definition ###


dash.register_page(
    __name__,
    path="/locations",
    title="tRacket",
    path_template="/locations/<device_id>",
)


def layout(device_id: str = None, **kwargs):
    leaflet_manager = LeafletMapComponentManager(locations)

    if device_id is None:
        map = leaflet_manager.get_map(device_id=device_id)
        layout = map

    else:
        map = leaflet_manager.get_map(device_id=device_id, style={"height": "50vh"})
        
        # load data for location
        data_manager.load_and_format_location_noise(location_id=device_id)
        
        # line plot
        plotter = TimeseriesPlotter(data_manager.location_noise)
        line_fig = plotter.plot()

        noise_line_graph = dcc.Graph(
            figure=line_fig,
            id=COMPONENT_ID.noise_line_graph,
            config={"displayModeBar": False},
        )

        # noise indicator
        plotter = MeanIndicatorPlotter(data_manager.location_noise)
        indicator_fig = plotter.plot()

        indicator_graph = dcc.Graph(
            figure=indicator_fig,
            id=COMPONENT_ID.mean_indicator,
            config={"displayModeBar": False},
        )

        # explanation
        explanation = dbc.Card(
            [
                # dbc.CardHeader(),
                dbc.CardBody(
                    [   
                        html.H4("Moderate Noise Level", className="card-title"),
                        html.P("This is some text explaining the noise level.", className="card-text"),
                    ]
                ),
            ],
            className="w-100 h-100",
            color="#FDCB80",
            style={"color": "black"},
        )

        layout = dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(indicator_graph, width=6), dbc.Col(explanation, width=6),
                    ],
                    className="g-0",
                ),
                dbc.Row(
                    [
                        dbc.Col(noise_line_graph, width=12),
                    ]
                ),
                dbc.Row([dbc.Col(map)]),
            ]
        )

    return layout
