"""
The main map page of the application.
"""

import dash
import dash_bootstrap_components as dbc
from src.data_loading.main import AppDataManager
from src.utils import Logging
from src.app_components import (
    LeafletMapComponentManager,
    LocationComponentManager,
    CallbackManager,
    COMPONENT_ID
)
from dash import callback, Input, Output, dcc, html, State

logger = Logging.get_console_logger(__name__)


### Data loading ###

data_manager = AppDataManager()
data_manager.load_and_format_locations()


### Graph component and Callback manager ###

location_component_manager = LocationComponentManager()

CallbackManager.initialize_callbacks()

### Dash Page Setup ###

dash.register_page(
    __name__,
    path="/locations",
    title="tRacket",
    path_template="/locations/<device_id>",
)

### CALLBACKS ###

# NOTE: need to be defined outside the layer() function for these to work

# @callback(
#     Output("clickdata", "children"),
#     Input(COMPONENT_ID.system_map, "clickData"),
# )
# def marker_click(data):
#     pass

### LAYOUT DEFINITION ###

def layout(device_id: str = None, **kwargs):
    leaflet_manager = LeafletMapComponentManager(data_manager.locations)
    if device_id is None:
        map = leaflet_manager.get_map()
        layout = map

    else:
        # get map for specific location
        map = leaflet_manager.get_map(
            device_id=device_id, style={"height": "50vh"}
        )

        # load data for location
        data_manager.load_and_format_location_noise(location_id=device_id)

        # explanation
        level_card = location_component_manager.get_explanation_card()

        # get components
        indicator = location_component_manager.get_mean_indicator(
            data_manager.location_noise
        )
        noise_line_graph = location_component_manager.get_noise_line_graph(
            data_manager.location_noise
        )

        # define layout
        layout = dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(indicator, width=6),
                        dbc.Col(level_card, width=6, align="center"),
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
