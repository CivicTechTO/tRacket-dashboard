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
from datetime import date, timedelta
from dash import dcc, html
import numpy as np

logger = Logging.get_console_logger(__name__)

### Data loading ###

data_manager = AppDataManager()

### Graph component and Callback manager ###

location_component_manager = LocationComponentManager(data_manager=data_manager)

callback_manager = CallbackManager(data_manager)
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
            leaflet_manager.set_locations(data_manager.location_info)
            map = leaflet_manager.get_map(
                device_id=device_id,
                style={"height": "300px"},
                radius=radius,
                active=active,
            )

            map_card = dbc.Card(
                [
                    dbc.CardHeader(html.H2(
                        [
                            html.I(className="fa-solid fa-map-location-dot"), 
                            " ",
                            f"{label} "
                        ], className="card-title")),
                    dbc.CardBody([map])
                ]
            )

            level_card = location_component_manager.get_level_card(
                "Current Noise Trend",
                data_manager.location_noise[Granularity.hourly],
                style={"height": "395px", "margin-bottom": "20px"},
            )

            raw_noise_line_graph = (
                location_component_manager.get_noise_line_graph(
                    data_manager.location_noise[Granularity.raw],
                    component_id=COMPONENT_ID.raw_noise_line_graph,
                )
            )

            hourly_noise_line_graph = (
                location_component_manager.get_noise_line_graph(
                    data_manager.location_noise[Granularity.hourly],
                    component_id=COMPONENT_ID.hourly_noise_line_graph,
                    bold_line=True,
                )
            )
            

            ### Date Picker ###

            # setup date
            end = data_manager.location_stats.loc[0, COLUMN.END]
            end = date(end.year, end.month, end.day)
            start = data_manager.location_stats.loc[0, COLUMN.START]
            start = date(start.year, start.month, start.day)
            start_default = end - timedelta(days=7)

            # setup date picker
            date_controls = location_component_manager.get_date_controls(
                min_date_allowed=start,
                max_date_allowed=end,
                start_default=start_default,
                end_default=end
            )

            line_graphs_card = dbc.Card(
                [
                    dbc.CardHeader(html.H2(
                        [
                            html.I(className="fa-solid fa-magnifying-glass-chart"), 
                            " ",
                            "Noise Analyzer"
                            ],
                         className="card-title")),
                    dbc.CardBody(
                        [
                            dbc.Row([dbc.Col([date_controls], lg=12, md=12)]),
                            dbc.Row([dbc.Col(hourly_noise_line_graph, lg=12, md=12)]),
                            dbc.Row([dbc.Col(raw_noise_line_graph, lg=12, md=12)]),
                        ]
                    )
                ]
            )

            # define layout
            layout = dbc.Container(
                [
                    location_component_manager.get_navbar(),
                    html.Br(),
                    dbc.Row(
                        [
                            dbc.Col(level_card, lg=6, md=12),
                            dbc.Col(map_card, lg=6, md=12),
                        ],
                    ),
                    html.Br(),
                    line_graphs_card
                ],
                fluid=True,
            )

    return layout
