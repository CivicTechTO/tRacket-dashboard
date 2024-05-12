from typing import List
from src.utils import COLUMN, load_config
from enum import StrEnum, auto
import pandas as pd
import dash_leaflet as dl


class COMPONENT_ID(StrEnum):
    """
    Component IDs for the app.
    """
    system_map = auto()


### Mapping ###


class LeafletMapComponentManager:
    def __init__(self, locations: pd.DataFrame) -> None:
        """
        Initialize with the location data.
        """
        self.config = load_config("src/config.ini")

        self._validate_data(locations)
        self.locations = locations

    def _validate_data(self, locations: pd.DataFrame) -> None:
        """
        Check that required columns are present.
        """
        assert COLUMN.LAT in locations.columns
        assert COLUMN.LON in locations.columns

    def _get_tile(self) -> dl.TileLayer:
        """
        Create the map tile layer.
        """
        tile_layer = dl.TileLayer(
            url=self.config["map"]["layer_url"],
            attribution=self.config["map"]["layer_attribution"],
        )

        return tile_layer

    def _get_markers(self) -> List[dl.CircleMarker]:
        """
        Build the markers for the map.
        """
        markers = [
            dl.CircleMarker(
                center=[lat, lon],
                radius=self.config["map"]["radius-pixel"],
                fillColor=self.config["map"]["marker_color"],
                color=self.config["map"]["marker_color"],
            )
            for lat, lon in zip(
                self.locations[COLUMN.LAT], self.locations[COLUMN.LON]
            )
        ]

        return markers

    def _get_map_center(self) -> tuple[float]:
        """
        Read the map center from the configs.
        """
        lat = float(self.config["constants"]["map_center_lat"])
        lon = float(self.config["constants"]["map_center_lon"])

        return (lat, lon)

    def get_map(self) -> dl.Map:
        """
        Create the location map.
        """
        map = dl.Map(
            [
                self._get_tile(),
                dl.LayerGroup(self._get_markers()),
                dl.GestureHandling(),
            ],
            center=self._get_map_center(),
            zoom=self.config["map"]["zoom"],
            style={"height": "100vh"},
            id=COMPONENT_ID.system_map
        )

        return map

