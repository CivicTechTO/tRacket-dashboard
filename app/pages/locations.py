"""
The main map page of the application.
"""

import dash
from dash import html
import dash_bootstrap_components as dbc
from src.data_loading.main import get_locations, create_api, AppDataManager
from src.utils import DataFormatter
from src.app_components import LeafletMapComponentManager

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
    map = leaflet_manager.get_map(device_id=device_id)

    if device_id is None:
        layout = map

    else:
        data_manager.load_and_format_location_noise(location_id=device_id)

        layout = dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(html.P("Indicator placeholder")),
                        dbc.Col(html.P("Line graph placeholder")),
                    ]
                ),
                dbc.Row([map]),
            ]
        )

    return layout
