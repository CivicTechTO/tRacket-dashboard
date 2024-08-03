"""
The main map page of the application.
"""

import dash
import dash_bootstrap_components as dbc
from src.data_loading.main import AppDataManager, Granularity
from src.utils import Logging, COLUMN
from src.app_components import (
    LeafletMapManager,
    LocationComponentManager,
    CallbackManager,
    COMPONENT_ID,
)
from dash import dcc, html
import numpy as np
import plotly.graph_objects as go


logger = Logging.get_console_logger(__name__)

### Data loading ###

data_manager = AppDataManager()

### Graph component and Callback manager ###

location_component_manager = LocationComponentManager(
    data_manager=data_manager
)

callback_manager = CallbackManager(data_manager=data_manager)
callback_manager.initialize_callbacks()

### Dash Page Setup ###

dash.register_page(
    __name__,
    path="/locations",
    title="tRacket Dashboard",
    path_template="/locations/<device_id>",
)


### LAYOUT DEFINITION ###

leaflet_manager = LeafletMapManager()


def layout(device_id: str = None, **kwargs):
    if device_id is None:
        data_manager.load_and_format_locations()
        leaflet_manager.set_locations(data_manager.locations)

        data_manager.locations[COLUMN.MARKER_COLOR] = np.where(
            data_manager.locations[COLUMN.ACTIVE],
            data_manager.config["map"]["marker_color_highlight"],
            data_manager.config["map"]["marker_color_inactive"],
        )
        map_card = leaflet_manager.get_map()
        layout = map_card

    else:
        data_manager.device_id = device_id

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
            label = data_manager.get_label(location_id=device_id)
            radius = data_manager.get_radius(location_id=device_id)
            active = data_manager.get_active_status(location_id=device_id)

            ### GET COMPONENTS ###

            # MAP CARD for specific location
            leaflet_manager.set_locations(data_manager.location_info)
            
            map = leaflet_manager.get_map(
                device_id=device_id,
                style={"height": "300px"},
                radius=radius,
                active=active,
            )

            map_card = location_component_manager.get_card(
                title=label,
                body=map,
                logo="fa-map-location-dot"
            )

            # NOISE LEVEL card
            level_card = location_component_manager.get_level_card()

            # LINE GRAPH card with date picker and download button
            line_graphs_card = location_component_manager.get_noise_line_graph_card()

            # NAVBAR
            nav_bar = location_component_manager.get_navbar()

            ### LAYOUT ###

            layout = dbc.Container(
                [
                    dcc.Store(id=COMPONENT_ID.raw_data_store),
                    dcc.Store(id=COMPONENT_ID.hourly_data_store),
                    nav_bar,
                    html.Br(),
                    dbc.Row(
                        [
                            dbc.Col(level_card, lg=6, md=12),
                            dbc.Col(map_card, lg=6, md=12),
                        ],
                    ),
                    html.Br(),
                    dbc.Row([line_graphs_card]),
                ],
                fluid=True,
            )

    return layout
