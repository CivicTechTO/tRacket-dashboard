"""
The main map page of the application.
"""
from typing import List
import dash
import configparser
from src.utils import COLUMN
from src.data_loading.main import get_locations, create_api
from src.data_loading_legacy import DataFormatter
import dash_leaflet as dl

### Configs & Settings ###

config = configparser.ConfigParser()
config.read("src/config.ini")

dash.register_page(__name__, title="tRacket")


### Data loading ###

api = create_api()
locations = get_locations(api)

# map string col names to enum
dataformatter = DataFormatter()
locations = dataformatter._string_col_names_to_enum(locations)

### Mapping ###

def get_tile() -> dl.TileLayer:
    """
    Create the map tile layer.
    """
    tile_layer = dl.TileLayer(
                url=config["map"]["layer_url"],
                attribution=config["map"]["layer_attribution"]
                )

    return tile_layer

# create location markers
def get_markers() -> List[dl.CircleMarker]:
    """
    Build the markers for the map
    """
    markers = [
        dl.CircleMarker(
            center=[lat, lon],
            radius=config["map"]["radius-pixel"],
            fillColor=config["map"]["marker_color"],
            color=config["map"]["marker_color"]
        )
        for lat, lon in zip(locations[COLUMN.LAT], locations[COLUMN.LON])
    ]

    return markers

def get_map_center() -> tuple[float]:
    """
    Read the map center from the configs.
    """
    lat = float(config["constants"]["map_center_lat"])
    lon = float(config["constants"]["map_center_lon"])

    return (lat, lon)

def layout(**kwargs):
    map = dl.Map(
        [
            get_tile(),
            dl.LayerGroup(get_markers()),
            dl.GestureHandling()
        ],
        center=get_map_center(),
        zoom=config["map"]["zoom"],
        style={"height": "100vh"},
    )

    return map
