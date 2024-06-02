from src.utils import COLUMN, load_config, get_last_time
from src.plotting import TimeseriesPlotter, MeanIndicatorPlotter
from enum import StrEnum, auto
import pandas as pd
import dash_leaflet as dl
from dash_extensions.javascript import assign
import dash_leaflet.express as dlx
from dash import callback, Input, Output, dcc, html, State, get_asset_url
import dash_bootstrap_components as dbc
from typing import List


class COMPONENT_ID(StrEnum):
    """
    Component IDs for the app.
    """

    system_map = auto()
    hourly_noise_line_graph = auto()
    mean_indicator = auto()
    mean_indicator_tooltip = auto()
    map_markers = auto()
    raw_noise_line_graphs = auto()
    redirect = auto()


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
                    selected_device[COLUMN.LABEL],
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
                dict(lat=lat, lon=lon, id=id, active=active, label=label)
                for lat, lon, id, label, active in zip(
                    self.locations[COLUMN.LAT],
                    self.locations[COLUMN.LON],
                    self.locations[COLUMN.DEVICEID],
                    self.locations[COLUMN.LABEL],
                    self.locations[COLUMN.ACTIVE],
                )
            ]
            markers = dlx.dicts_to_geojson(markers)

            on_each_feature = assign(
                """function(feature, layer, context){
                if (feature.properties.active) {{ 
                    var active = "<b>Active Location</b>";
                    }} else {{
                    var active = "<b>Inactive Location</b>";
                }};
                if (feature.properties.label) {{
                    var label = feature.properties.label;
                }} else {{
                    var label = "";
                }};
                if (!feature.properties.cluster) {{
                    layer.bindTooltip(`${active}<br>${label}`)
                }};
            }"""
            )

            markers = dl.GeoJSON(
                data=markers,
                pointToLayer=assign(self._point_to_layer_system_map()),
                clusterToLayer=assign(self._cluster_to_layer()),
                onEachFeature=on_each_feature,
                cluster=True,
                zoomToBounds=True,
                zoomToBoundsOnClick=True,
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
                        color: "{self.config["map"]["marker_color_highlight"]}"
                    }});
                    return L.marker(latlng, {{icon : icon}})
                }}"""

    def _point_to_layer_system_map(self) -> str:
        """
        How to render individual markers on the map client-side?
        """
        return f"""
                function(feature, latlng, context){{
                    if (feature.properties.active) {{
                        var color = "{self.config["map"]["marker_color_highlight"]}";
                        var opcaity = 0.8;
                    }} else {{
                        var color = "{self.config["map"]["marker_color_inactive"]}";
                        var opacity = 0.4;
                    }};
                    return L.circleMarker(latlng, 
                    {{
                        radius: {self.config["map"]["radius-pixel"]}, 
                        fillColor: color, 
                        fillOpacity: opacity,
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
                        radius: {self.config["map"]["radius-meter"]}, 
                        color: "{self.config["map"]["marker_color_highlight"]}", 
                        fillColor: "{self.config["map"]["marker_color_highlight"]}", 
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

    def get_noise_line_graph(self, location_noise: pd.DataFrame, component_id: COMPONENT_ID, bold_line: bool = False) -> dcc.Graph:
        """
        Create the noise graph component.
        """
        # line plot
        plotter = TimeseriesPlotter(location_noise)
        line_fig = plotter.plot(bold_line=bold_line)

        noise_line_graph = dcc.Graph(
            figure=line_fig,
            id=component_id,
            config={
                "displayModeBar": True,
                "displaylogo": False,
                "modeBarButtonsToRemove": [
                    "zoom",
                    "zoomIn",
                    "zoomOut",
                    "pan",
                    "select",
                    "resetScale",
                    "download",
                    "lasso2d",
                    "toImage",
                ],
            },
        )

        return noise_line_graph

    def _get_mean_indicator(self, location_noise: pd.DataFrame) -> html.Div:
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

    def get_level_card(
        self,
        label: str,
        location_noise: pd.DataFrame,
        style: dict = {"height": "100vh"},
    ) -> dbc.Card:

        last_time = get_last_time(location_noise)

        card = dbc.Card(
            [
                dbc.CardHeader(html.H2(label, className="card-title")),
                dbc.CardBody(
                    [
                        html.P(
                            "The last hourly average received from the device and percentage change since the hour before."
                        ),
                        html.P(f"Time: {last_time}"),
                        self._get_mean_indicator(location_noise),
                    ]
                ),
            ],
            className="moderate-card",
            style=style,
        )
        return card

    def get_navbar(self) -> dbc.NavbarSimple:
        """
        Get the navigation bar.
        """
        navbar = dbc.NavbarSimple(
            children=[],
            brand=dbc.Container(
                [
                    html.A(
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Img(
                                        src=get_asset_url("tracket_logo.svg"),
                                        height="30px",
                                    )
                                )
                            ],
                            align="center",
                            className="g-0",
                        ),
                        href="https://tracket.info/",
                        style={"textDecoration": "none"},
                    ),
                ]
            ),
            color="#2D2D32",
            dark=True,
        )
        return navbar


class CallbackManager:
    """
    Class that organizes and  initializes the Dash app callbacks on app start.
    """

    @classmethod
    def initialize_callbacks(cls):
        pass
