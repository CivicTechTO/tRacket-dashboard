"""
The main map page of the application.
"""

import dash
from src.data_loading.main import get_locations, create_api
from src.data_loading_legacy import DataFormatter
from src.app_components import LeafletMapComponentManager

### Data loading ###

api = create_api()
locations = get_locations(api)

# map string col names to enum
dataformatter = DataFormatter()
locations = dataformatter._string_col_names_to_enum(locations)


### Dash Page Definition ###


dash.register_page(__name__, title="tRacket")


def layout(**kwargs):
    leaflet_manager = LeafletMapComponentManager(locations)
    map = leaflet_manager.get_map()

    return map
