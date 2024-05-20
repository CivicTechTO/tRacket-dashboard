from typing import List, Optional
from src.utils import COLUMN, load_config
from src.data_loading.main import AppDataManager
from src.plotting import TimeseriesPlotter, MeanIndicatorPlotter
from enum import StrEnum, auto
import pandas as pd
import dash_leaflet as dl
from dash import callback, Input, Output, dcc, html, State
import dash_bootstrap_components as dbc
from abc import abstractclassmethod


class COMPONENT_ID(StrEnum):
    """
    Component IDs for the app.
    """

    system_map = auto()
    noise_line_graph = auto()
    mean_indicator = auto()


# class AbstractAppManager(object):
#     """
#     Base class for managing app components and making data available through the AppDataManager.
#     """

#     _config = load_config()
#     app_data_manager: AppDataManager = None

#     @classmethod
#     def _set_app_data_manager(cls, app_data_manager: AppDataManager) -> None:
#         cls.app_data_manager = app_data_manager

#     @abstractclassmethod
#     def initialize(
#         cls, app_data_manager: Optional[AppDataManager] = None
#     ) -> None:
#         if app_data_manager:
#             cls._set_app_data_manager(app_data_manager)
#         pass


### Mapping ###


class LeafletMapComponentManager:
    def __init__(self, locations: pd.DataFrame) -> None:
        """
        Initialize with the location data.
        """
        self.config = load_config()

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

    def _get_markers(self, device_id: str = None) -> List[dl.CircleMarker]:
        """
        Build the markers for the map.
        """
        if device_id:
            selected_device = self.locations[
                self.locations[COLUMN.DEVICEID] == device_id
            ]

            lat = list(selected_device[COLUMN.LAT])[0]
            lon = list(selected_device[COLUMN.LON])[0]

            selected_device_marker = dl.Circle(
                center=[lat, lon],
                radius=self.config["map"]["radius-meter"],
                fillColor=self.config["map"]["marker_color_highlight"],
                color=self.config["map"]["marker_color_highlight"],
            )

            markers = [selected_device_marker]

        else:
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

    def _get_map_center(self, device_id: str = None) -> tuple[float]:
        """
        Read the map center from the configs.
        """
        if device_id:
            device_row = self.locations[
                self.locations[COLUMN.DEVICEID] == device_id
            ]

        if device_id and device_row.shape[0] > 0:
            lat = list(device_row[COLUMN.LAT])[0]
            lon = list(device_row[COLUMN.LON])[0]
        else:
            lat = float(self.config["constants"]["map_center_lat"])
            lon = float(self.config["constants"]["map_center_lon"])

        return (lat, lon)

    def get_map(self, device_id: str = None, style: dict = {"height": "100vh"}) -> dl.Map:
        """
        Create the location map.
        """

        zoom = self._get_zoom(default=(device_id is None))

        map = dl.Map(
            [
                self._get_tile(),
                dl.LayerGroup(self._get_markers(device_id=device_id)),
                dl.GestureHandling(),
            ],
            center=self._get_map_center(device_id=device_id),
            zoom=zoom,
            style=style,
            id=COMPONENT_ID.system_map,
        )

        return map

    def _get_zoom(self, default: bool = True):
        """
        Find level of zoom, default is system level (higher), non defailt is device focus.
        """
        default_zoom = int(self.config["map"]["zoom"])
        zoom = default_zoom if default else default_zoom + 4

        return zoom


class LocationComponentManager():
    """
    Class to collect and initialize the graph components for the app.
    """

    def initialize(self) -> None:
        """
        Main call to setup all graph components for the app.
        """
        self.config = load_config()


    def get_noise_line_graph(self, location_noise: pd.DataFrame) -> dcc.Graph:
        """
        Create the noise graph component.
        """
        # line plot
        plotter = TimeseriesPlotter(location_noise)
        line_fig = plotter.plot()

        noise_line_graph = dcc.Graph(
            figure=line_fig,
            id=COMPONENT_ID.noise_line_graph,
            config={"displayModeBar": False},
        )

        return noise_line_graph
    
    def get_mean_indicator(self, location_noise: pd.DataFrame) -> tuple[dcc.Graph, dbc.Tooltip]:
        """
        Create the indicator with tooltip.
        """

        # noise indicator with toolip
        plotter = MeanIndicatorPlotter(location_noise)
        indicator_fig = plotter.plot()

        indicator_graph = dcc.Graph(
            figure=indicator_fig,
            id=COMPONENT_ID.mean_indicator,
            config={"displayModeBar": False},
        )

        indicator_tooltip = dbc.Tooltip(
            f"Average noise level in the past hour and relative change since the hour prior.",
            target=COMPONENT_ID.mean_indicator,
            placement="bottom",
        )


        return indicator_graph, indicator_tooltip

    def get_explanation_card(self) -> dbc.Card:
        card = dbc.Card(
            [
                dbc.CardHeader(html.H3("Moderate Noise Level", className="card-title")),
                dbc.CardBody(
                    [   
                        html.P("Some text explaining the noise.")
                    ]
                ),
            ],
            className="moderate-card",
        )
        return card
