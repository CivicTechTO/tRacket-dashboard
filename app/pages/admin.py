"""
Admin page for system maintenance and monitoring.
"""
import pandas as pd
import numpy as np
import dash
import dash_bootstrap_components as dbc
from src.data_loading.main import AppDataManager
from src.utils import Logging, COLUMN
from src.app_components import (
    LeafletMapManager,
    AdminComponentManager,
)
from dash import html

dash.register_page(
    __name__,
    path="/admin",
    title="tRacket Admin",
)

logger = Logging.get_console_logger(__name__)

### Data loading ###

data_manager = AppDataManager()

### Layout ###
leaflet_manager = LeafletMapManager()
admin_component_manager = AdminComponentManager()


def layout(**kwargs):
    # load data
    data_manager.load_and_format_locations()
    data_manager.load_all_location_stats()

    admin_df = pd.concat([data_manager.all_location_stats, data_manager.locations], axis=1)

    # set up admin table
    table_columns = [
        COLUMN.DEVICEID,
        COLUMN.LABEL,
        COLUMN.END,
        COLUMN.ACTIVE,
        COLUMN.COUNT,
        COLUMN.RADIUS,
        COLUMN.SENDING_DATA
    ]
    table = admin_component_manager.get_data_table(
        admin_df[table_columns]
    )

    # set map
    leaflet_manager.set_locations(
        admin_df[
            [
                COLUMN.DEVICEID,
                COLUMN.LABEL,
                COLUMN.ACTIVE,
                COLUMN.LAT,
                COLUMN.LON,
                COLUMN.SENDING_DATA
            ]
        ]
    )
    map = leaflet_manager.get_map(
        style={"height": "50vh", "marginBottom": "10px"}
    )

    indicators = {
        "Locations": admin_df.shape[0],
        "Active": admin_df[admin_df[COLUMN.ACTIVE] == True].shape[0],
        "Sending Data": admin_df[admin_df[COLUMN.END] > limit].shape[0],
    }

    indicator_row = admin_component_manager.get_indicators(indicators)

    nav_bar = admin_component_manager.get_navbar()

    layout = dbc.Container(
        [
            dbc.Row([nav_bar]),
            html.Br(),
            dbc.Row([dbc.Col([map])]),
            html.Br(),
            indicator_row,
            dbc.Row([dbc.Col([table])]),
        ],
        fluid=True
    )

    return layout
