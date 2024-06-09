"""
The main map page of the application.
"""

import dash
import dash_bootstrap_components as dbc
from src.data_loading.main import AppDataManager, Granularity
from src.utils import Logging
from src.app_components import (
    LeafletMapManager,
    LocationComponentManager,
    CallbackManager,
    COMPONENT_ID,
)
from dash import Input, Output, dcc, html, clientside_callback

logger = Logging.get_console_logger(__name__)


### Data loading ###

data_manager = AppDataManager()

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


### LAYOUT DEFINITION ###

leaflet_manager = LeafletMapManager()

def layout(device_id: str = None, **kwargs):
    data_manager.load_and_format_locations()
    leaflet_manager.set_locations(data_manager.locations)

    if device_id is None:
        map = leaflet_manager.get_map()
        layout = map

    else:
        # load data for location
        data_manager.load_and_format_location_stats(location_id=device_id)
        data_manager.load_and_format_location_info(location_id=device_id)

        if data_manager.is_noise_available(location_id=device_id):
            logger.info(f"No noise data available yet at the location.")
            redirect = dcc.Location(
                pathname="/not_found_404.py", id=COMPONENT_ID.redirect
            )
            layout = dbc.Container([redirect])

        else:
            data_manager.load_and_format_location_noise(
                location_id=device_id, granularity=Granularity.hourly
            )
            data_manager.load_and_format_location_noise(
                location_id=device_id, granularity=Granularity.raw
            )

            label = data_manager.get_label(location_id=device_id)
            radius = data_manager.get_radius(location_id=device_id)
            active = data_manager.get_active_status(location_id=device_id)

            ### Get Components ###

            # get map for specific location
            map = leaflet_manager.get_map(
                device_id=device_id,
                style={"height": "350px"},
                radius=radius,
                active=active,
            )

            level_card = location_component_manager.get_level_card(
                label,
                data_manager.location_noise[Granularity.hourly],
                style={"height": "350px", "margin-bottom": "20px"},
            )

            hourly_noise_line_graph = (
                location_component_manager.get_noise_line_graph(
                    data_manager.location_noise[Granularity.hourly],
                    component_id=COMPONENT_ID.hourly_noise_line_graph,
                    bold_line=True,
                )
            )

            raw_noise_line_graph = (
                location_component_manager.get_noise_line_graph(
                    data_manager.location_noise[Granularity.raw],
                    component_id=COMPONENT_ID.raw_noise_line_graph,
                )
            )

            # define layout
            layout = dbc.Container(
                [
                    location_component_manager.get_navbar(),
                    html.Br(),
                    dbc.Row(
                        [
                            dbc.Col(level_card, lg=6, md=12),
                            dbc.Col(map, lg=6, md=12),
                        ],
                    ),
                    html.Br(),
                    dbc.Row([dbc.Col(hourly_noise_line_graph, lg=12, md=12)]),
                    dbc.Row([dbc.Col(raw_noise_line_graph, lg=12, md=12)]),
                ],
                fluid=True,
            )

    return layout
