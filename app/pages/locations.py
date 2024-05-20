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


### Dash Page Definition ###

dash.register_page(
    __name__,
    path="/locations",
    title="tRacket",
    path_template="/locations/<device_id>",
)


def layout(device_id: str = None, **kwargs):
    leaflet_manager = LeafletMapComponentManager(data_manager.locations)

    if device_id is None:
        map = leaflet_manager.get_map(device_id=device_id)
        layout = map

    else:
        # get map for specific location
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

        # noise indicator with toolip
        plotter = MeanIndicatorPlotter(data_manager.location_noise)
        indicator_fig = plotter.plot()

        indicator_graph = dcc.Graph(
            figure=indicator_fig,
            id=COMPONENT_ID.mean_indicator,
            config={"displayModeBar": False},
        )

        indicator_tooltip = dbc.Tooltip(
            f"Average noise level in the past hour and relative change since the hour prior.",
            target=COMPONENT_ID.mean_indicator,
            placement="bottom",
        )

        indicator = html.Div([html.Div([indicator_graph]), html.Div([indicator_tooltip])])

        # explanation
        level_card = dbc.Card(
            [
                dbc.CardHeader(html.H3("Moderate Noise Level", className="card-title")),
                dbc.CardBody(
                    [   
                        html.P("Some text explaining the noise.")
                    ]
                ),
            ],
            className="moderate-card",
        )

        layout = dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(indicator, width=6), dbc.Col(level_card, width=6, align="center"),
                    ],
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
