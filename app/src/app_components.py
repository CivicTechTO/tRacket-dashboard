from src.utils import COLUMN, load_config
from src.plotting import TimeseriesPlotter, MeanIndicatorPlotter
from enum import StrEnum, auto
import pandas as pd
import dash_leaflet as dl
from dash_extensions.javascript import assign
import dash_leaflet.express as dlx
from dash import callback, Input, Output, dcc, html, State
import dash_bootstrap_components as dbc
from typing import List


class COMPONENT_ID(StrEnum):
    """
    Component IDs for the app.
    """

    system_map = auto()
    noise_line_graph = auto()
    mean_indicator = auto()
    mean_indicator_tooltip = auto()
    map_markers = auto()


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
        assert COLUMN.DEVICEID in locations.columns
        assert COLUMN.ACTIVE in locations.columns
        assert COLUMN.LABEL in locations.columns

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

            markers = [
                dict(lat=lat, lon=lon, id=id, tooltip=label)
                for lat, lon, id, label in zip(
                    selected_device[COLUMN.LAT],
                    selected_device[COLUMN.LON],
                    selected_device[COLUMN.DEVICEID],
                    selected_device[COLUMN.LABEL]
                )
            ]
            markers = dlx.dicts_to_geojson(markers)
            
            markers = dl.GeoJSON(
                data=markers,
                pointToLayer=assign(self._point_to_layer_location_map()),
                id=f"marker-{device_id}",
            )

        else:
            markers = [
                dict(lat=lat, lon=lon, id=id, tooltip=label)
                for lat, lon, id, label in zip(
                    self.locations[COLUMN.LAT],
                    self.locations[COLUMN.LON],
                    self.locations[COLUMN.DEVICEID],
                    self.locations[COLUMN.LABEL]
                )
            ]
            markers = dlx.dicts_to_geojson(markers)
            
            markers = dl.GeoJSON(
                data=markers,
                pointToLayer=assign(self._point_to_layer_system_map()),
                clusterToLayer=assign(self._cluster_to_layer()),
                cluster=True,
                zoomToBounds=True,
                id=COMPONENT_ID.map_markers,
            )

        self.markers = markers

        return markers

    def _cluster_to_layer(self) -> str:
        """
        How to render clusters on the map client-side?
        """
        return f"""function(feature, latlng, index, context){{
                    // Modify icon background color.
                    const scatterIcon = L.DivIcon.extend({{
                        createIcon: function(oldIcon) {{
                            let icon = L.DivIcon.prototype.createIcon.call(this, oldIcon);
                            icon.style.backgroundColor = this.options.color;
                            return icon;
                        }}
                    }})
                    // Render a circle with the number of leaves written in the center.
                    const icon = new scatterIcon({{
                        html: '<div style="background-color:white;"><span>' + feature.properties.point_count_abbreviated + '</span></div>',
                        className: "marker-cluster",
                        iconSize: L.point(40, 40),
                        color: "{self.config["map"]["marker_color"]}"
                    }});
                    return L.marker(latlng, {{icon : icon}})
                }}"""

    def _point_to_layer_system_map(self) -> str:
        """
        How to render individual markers on the map client-side?
        """
        return f"""
                function(feature, latlng, context){{
                    return L.circleMarker(latlng, 
                    {{
                        radius: {self.config["map"]["radius-pixel"]}, 
                        fillColor: "{self.config["map"]["marker_color"]}", 
                        fillOpacity: 0.8
                    }});  // render a simple circle marker
                }}
                """
    
    def _point_to_layer_location_map(self) -> str:
        """
        How to render individual markers on the map client-side?
        """
        return f"""
                function(feature, latlng, context){{
                    return L.circle(latlng, 
                    {{
                        radius: {200}, 
                        fillColor: "{self.config["map"]["marker_color_highlight"]}", 
                        color: "{self.config["map"]["marker_color_highlight"]}", 
                        fillOpacity: 0.4
                    }});  // render a simple circle marker
                }}
                """

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

    def get_map(
        self, device_id: str = None, style: dict = {"height": "100vh"}
    ) -> dl.Map:
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


class LocationComponentManager:
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

    def get_mean_indicator(self, location_noise: pd.DataFrame) -> html.Div:
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
            id=COMPONENT_ID.mean_indicator_tooltip,
        )

        return html.Div([indicator_graph, indicator_tooltip])

    def get_explanation_card(self) -> dbc.Card:
        card = dbc.Card(
            [
                dbc.CardHeader(
                    html.H3("Moderate Noise Level", className="card-title")
                ),
                dbc.CardBody([html.P("Some text explaining the noise.")]),
            ],
            className="moderate-card",
        )
        return card


class CallbackManager:
    """
    Class that organizes and  initializes the Dash app callbacks on app start.
    """

    @classmethod
    def initialize_callbacks(cls):
        pass
