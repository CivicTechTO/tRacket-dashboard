"""
The main map page of the application.
"""

import dash
import dash_bootstrap_components as dbc
from src.data_loading.main import AppDataManager, Granularity
from src.utils import Logging, COLUMN
from src.app_components import (
    LeafletMapComponentManager,
    LocationComponentManager,
    CallbackManager,
    COMPONENT_ID,
)
from dash import callback, Input, Output, dcc, html, State, clientside_callback

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

clientside_callback(
    """
    function(feature, n_clicks) {
        var base_url = window.location.href;
        console.log(feature)
        if (!feature.properties.cluster) {
            var url = new URL("locations/".concat(feature.properties.id), base_url);
            console.log(`Redirecting to ${url}`);
            window.open(url, '_blank');
        }
    }
    """,
    Output(COMPONENT_ID.map_markers, "hideout"),
    Input(COMPONENT_ID.map_markers, "clickData"),
    Input(COMPONENT_ID.map_markers, "n_clicks"),
    prevent_initial_call=True,
)

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
        data_manager.load_and_format_location_noise(
            location_id=device_id, granularity=Granularity.hourly
        )
        data_manager.load_and_format_location_noise(
            location_id=device_id, granularity=Granularity.raw
        )
        data_manager.load_and_format_location_info(location_id=device_id)

        info = data_manager.location_info.to_dict("records")[0]
        label = info[COLUMN.LABEL]
        radius = info[COLUMN.RADIUS]

        # get components
        level_card = location_component_manager.get_level_card(
            label,
            data_manager.location_noise[Granularity.hourly],
            style={"height": "50vh"},
        )

        noise_line_graph = location_component_manager.get_noise_line_graph(
            data_manager.location_noise[Granularity.hourly]
        )

        nav_bar = location_component_manager.get_navbar()

        # define layout
        layout = dbc.Container(
            [
                nav_bar,
                html.Br(),
                dbc.Row(
                    [
                        dbc.Col(level_card, lg=6, md=12),
                        dbc.Col(map, lg=6, md=12),
                    ],
                ),
                html.Br(),
                dbc.Row([dbc.Col(noise_line_graph, lg=12, md=12)]),
            ],
            fluid=True,
        )

    return layout
