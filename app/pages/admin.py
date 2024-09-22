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

    stats = []
    for device_id in data_manager.locations[COLUMN.DEVICEID]:
        device_stat = data_manager.load_and_format_location_stats(
            location_id=device_id
        )
        stats.append(device_stat)
    stats = pd.concat(stats, axis=0, ignore_index=True)

    admin_df = pd.concat([stats, data_manager.locations], axis=1)

    table_columns = [
        COLUMN.DEVICEID,
        COLUMN.LABEL,
        COLUMN.END,
        COLUMN.ACTIVE,
        COLUMN.COUNT,
        COLUMN.RADIUS,
    ]

    limit = pd.Timestamp("now") + pd.Timedelta(-4, unit="H")
    limit += pd.Timedelta(-1, unit="H")
    admin_df[COLUMN.SENDING_DATA] = admin_df[COLUMN.END] > limit
    
    admin_df[COLUMN.MARKER_COLOR] = np.where(
        admin_df[COLUMN.SENDING_DATA], "#2C7BB2", "#545454"
    )
    
    table = admin_component_manager.get_data_table(
        admin_df[table_columns], limit
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
                COLUMN.MARKER_COLOR,
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
