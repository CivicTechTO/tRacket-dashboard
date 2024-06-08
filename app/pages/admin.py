"""
Admin page for system maintenance and monitoring.
"""
import pandas as pd
import datetime
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
from dash import Input, Output, dcc, html, clientside_callback, dash_table

dash.register_page(
    __name__,
    path="/admin",
    title="tRacket Admin",
)

logger = Logging.get_console_logger(__name__)

### Data loading ###

data_manager = AppDataManager()
data_manager.load_and_format_locations()

### Layout ###

def layout(**kwargs):
    leaflet_manager = LeafletMapComponentManager(data_manager.locations)
    map = leaflet_manager.get_map(style={"height": "50vh", "margin-bottom": "10px"})
    
    stats = []
    info = []
    for device_id in data_manager.locations[COLUMN.DEVICEID]:
        device_stat = data_manager.load_and_format_location_stats(location_id=device_id)
        device_info = data_manager.load_and_format_location_info(location_id=device_id)
        stats.append(device_stat)
        info.append(device_info)
    
    stats = pd.concat(stats, axis=0)
    stats[COLUMN.DEVICEID] = data_manager.locations[COLUMN.DEVICEID].values

    info = pd.concat(info, axis=0)
    
    admin_df = pd.concat([stats, info], axis=1)
    admin_df = admin_df[[COLUMN.DEVICEID, COLUMN.LABEL, COLUMN.END, COLUMN.ACTIVE, COLUMN.COUNT, COLUMN.RADIUS]]
    admin_df = admin_df.sort_values(COLUMN.END, ascending=False)
    admin_df = data_manager.data_formatter._enum_col_names_to_string(admin_df)
    
    limit = (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat()

    table = dash_table.DataTable(
        data=admin_df.to_dict('records'),
        sort_action='native',
        style_data_conditional=[
            {
                'if': {
                    'filter_query': f'{{end}} > {limit}',
                },
                'backgroundColor': '#2C7BB2',
                'color': 'white'
            },
        ]
        )

    layout = dbc.Container(
        [
            dbc.Row([dbc.Col([map])]),
            dbc.Row([dbc.Col([table])])
        ]
    )
    
    return layout