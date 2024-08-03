from src.utils import (
    COLUMN,
    load_config,
    get_last_time,
    DataFormatter,
    date_to_string,
)
from src.plotting import (
    TimeseriesPlotter,
    MeanIndicatorPlotter,
    NumberIndicator,
)
from src.data_loading.main import AppDataManager, Granularity
import plotly.graph_objects as go
from enum import StrEnum, auto
import pandas as pd
import dash_leaflet as dl
from dash_extensions.javascript import assign
import dash_leaflet.express as dlx
from dash import dcc, html, get_asset_url
import dash_bootstrap_components as dbc
from typing import List, Dict
from datetime import datetime, date, timedelta
from dash import (
    callback,
    Input,
    Output,
    dcc,
    html,
    clientside_callback,
    Patch,
    dash_table,
)
import dash


class COMPONENT_ID(StrEnum):
    """
    Component IDs for the app.
    """
    redirect = auto()
    
    # maps
    system_map = auto()
    map_markers = auto()
    
    # aggregate indicator
    mean_indicator = auto()
    mean_indicator_tooltip = auto()
    
    # noise analyzer
    hourly_noise_line_graph = auto()
    raw_noise_line_graph = auto()
    date_picker = auto()
    download_button = auto()
    download_csv = auto()
    
    # data stores
    hourly_data_store = auto()
    last_update_text = auto()
    raw_data_store = auto()


### Mapping ###


class LeafletMapManager:
    def __init__(self) -> None:
        """
        Initialize with the location data.
        """
        self.config = load_config()

        self.locations = None

        self._assign_clientside_js_functions()

    def set_locations(self, locations: pd.DataFrame) -> None:
        self._validate_data(locations)
        self.locations = locations

    def _assign_clientside_js_functions(self) -> None:
        """
        Assign JS functions that are used for rendering leaflet markers.
        """
        self._assign_on_each_feature()
        self._assign_point_to_layer_system_map()
        self._assign_cluster_to_layer()
        self._assign_point_to_layer_location_map()

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

    def _get_markers(
        self, device_id: str = None, radius: int = None, active: bool = True
    ) -> List[dl.CircleMarker]:
        """
        Build the markers for the map.
        """

        if device_id:
            selected_device = self.locations[
                self.locations[COLUMN.DEVICEID] == device_id
            ]

            markers = [
                dict(lat=lat, lon=lon, id=id, label=label, active=active)
                for lat, lon, id, label, active in zip(
                    selected_device[COLUMN.LAT],
                    selected_device[COLUMN.LON],
                    selected_device[COLUMN.DEVICEID],
                    selected_device[COLUMN.LABEL],
                    selected_device[COLUMN.ACTIVE],
                )
            ]
            markers = dlx.dicts_to_geojson(markers)

            if active:
                color = self.config["map"]["marker_color_highlight"]
            else:
                color = self.config["map"]["marker_color_inactive"]

            radius = max(int(radius), int(self.config["map"]["radius-meter"]))

            markers = dl.GeoJSON(
                data=markers,
                pointToLayer=self._point_to_layer_location_map,
                onEachFeature=self._on_each_feature,
                id=f"marker-{device_id}",
                hideout={"radius": radius, "color": color},
            )

        else:
            markers = [
                dict(
                    lat=lat,
                    lon=lon,
                    id=id,
                    active=active,
                    label=label,
                    marker_color=color,
                )
                for lat, lon, id, label, active, color in zip(
                    self.locations[COLUMN.LAT],
                    self.locations[COLUMN.LON],
                    self.locations[COLUMN.DEVICEID],
                    self.locations[COLUMN.LABEL],
                    self.locations[COLUMN.ACTIVE],
                    self.locations[COLUMN.MARKER_COLOR],
                )
            ]
            markers = dlx.dicts_to_geojson(markers)

            markers = dl.GeoJSON(
                data=markers,
                pointToLayer=self._point_to_layer_system_map,
                clusterToLayer=self._cluster_to_layer,
                onEachFeature=self._on_each_feature,
                cluster=True,
                zoomToBounds=True,
                zoomToBoundsOnClick=True,
                id=COMPONENT_ID.map_markers,
            )

        self.markers = markers

        return markers

    def _assign_on_each_feature(self) -> None:
        """
        Client-side hover template.
        """
        self._on_each_feature = assign(
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

    def _assign_cluster_to_layer(self) -> None:
        """
        How to render clusters on the map client-side?
        """
        self._cluster_to_layer = assign(
            f"""function(feature, latlng, index, context){{
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
                        color: "{self.config["map"]["cluster_color"]}"
                    }});
                    return L.marker(latlng, {{icon : icon}})
                }}"""
        )

    def _assign_point_to_layer_system_map(self) -> None:
        """
        How to render individual markers on the map client-side?
        """
        self._point_to_layer_system_map = assign(
            f"""
                function(feature, latlng, context){{
                    return L.circleMarker(latlng, 
                    {{
                        radius: {self.config["map"]["radius-pixel"]}, 
                        fillColor: feature.properties.marker_color, 
                        fillOpacity: 0.8,
                    }});  // render a simple circle marker
                }}
                """
        )

    def _assign_point_to_layer_location_map(self) -> str:
        """
        How to render individual markers on the map client-side?
        """

        self._point_to_layer_location_map = assign(
            f"""
                function(feature, latlng, context){{
                    return L.circle(latlng, 
                    {{
                        radius: context.hideout["radius"], 
                        color: context.hideout["color"], 
                        fillColor: context.hideout["color"], 
                        fillOpacity: 0.4
                    }});  // render a simple circle marker
                }}
                """
        )

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
        self,
        device_id: str = None,
        style: dict = {"height": "100vh"},
        radius: int = None,
        active: bool = True,
    ) -> dl.Map:
        """
        Create the location map.
        """

        zoom = self._get_zoom(default=(device_id is None))

        map = dl.Map(
            [
                self._get_tile(),
                dl.LayerGroup(
                    self._get_markers(
                        device_id=device_id, radius=radius, active=active
                    )
                ),
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
        zoom = default_zoom if default else default_zoom + 6

        return zoom


class AbstractComponentManager:
    """
    Base class for managing components. Create a component page for each separate page of the dashboard.
    """

    def __init__(self) -> None:
        self.config = load_config()

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


class AdminComponentManager(AbstractComponentManager):
    """
    Manage components for the admin page.
    """

    def __init__(self) -> None:
        super().__init__()
        self.data_formatter = DataFormatter()

    def get_data_table(
        self, admin_df: pd.DataFrame, limit: datetime
    ) -> dash_table.DataTable:
        """
        Create a data table component with devices sending data actively highlighted.
        """
        assert (
            COLUMN.END in admin_df.columns
        ), "Dataframe should have an END column."

        admin_df = admin_df.sort_values(COLUMN.END, ascending=False)
        admin_df_plain = self.data_formatter._enum_col_names_to_string(
            admin_df
        )

        table = dash_table.DataTable(
            data=admin_df_plain.to_dict("records"),
            sort_action="native",
            style_data_conditional=[
                {
                    "if": {
                        "filter_query": f"{{end}} > {limit.isoformat()}",
                    },
                    "backgroundColor": "#2C7BB2",
                    "color": "white",
                },
            ],
        )

        return table

    def get_indicators(self, indicators: Dict[str, float | int]) -> dbc.Row:
        """
        Create a row of indicator graphs.
        """
        plotter = NumberIndicator()

        row = []
        for title, value in indicators.items():
            fig = plotter.plot(value=value, title=title)
            col = dbc.Col(
                dcc.Graph(
                    figure=fig,
                    config={"displayModeBar": False},
                    style={"height": "20vh"},
                )
            )
            row.append(col)

        return dbc.Row(children=row)


class LocationComponentManager(AbstractComponentManager):
    """
    Class to collect and initialize the components for the location page.
    """

    def __init__(self, data_manager: AppDataManager) -> None:
        super().__init__()
        self.data_manager = data_manager

    def get_card(self, title: str, body: object, logo: str, style: dict = dict()):
        """
        Create a dbc.Card() component with the given title, body and fontawesome logo.
        """
        card_header = dbc.CardHeader(
            html.H2(
                [
                    html.I(className=f"fa-solid {logo}"),
                    html.Span(
                        style={
                            "display": "inline-block",
                            "width": 25,
                        }
                    ),
                    html.Span(title),
                ],
                className="card-title",
            ),
        )
        card = dbc.Card([card_header, dbc.CardBody([body])], style=style)
        
        return card

    def _get_noise_line_graph(
        self,
        component_id: COMPONENT_ID,
    ) -> dcc.Graph:
        """
        Create an empty noise graph component which can be updated using callbacks.
        """
        noise_line_graph = dcc.Graph(
                figure=go.Figure(),
                id=component_id,
                style={"visibility": "hidden"},
            )

        return noise_line_graph

    def get_noise_line_graph_card(self) -> dbc.Card:
        """
        Create the card component holding the noise line graphs.
        """
        raw_noise_line_graph = self._get_noise_line_graph(COMPONENT_ID.raw_noise_line_graph)
        hourly_noise_line_graph = self._get_noise_line_graph(COMPONENT_ID.hourly_noise_line_graph)

        ### Date Picker ###

        # setup date picker
        date_controls = self._get_date_controls()

        # download button
        download_button = self._get_download_button()

        noise_line_card_body = dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(date_controls, lg=3, md=3),
                                dbc.Col(download_button, lg=2, md=2),
                            ]
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Spinner(hourly_noise_line_graph),
                                    lg=12,
                                    md=12,
                                )
                            ]
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Spinner(raw_noise_line_graph),
                                    lg=12,
                                    md=12,
                                )
                            ]
                        ),
                    ]
                )

        line_graphs_card = self.get_card(
            title="Noise Analyzer",
            body=noise_line_card_body,
            logo="fa-magnifying-glass-chart",
        )

        return line_graphs_card

    def _get_mean_indicator(self) -> html.Div:
        """
        Create the indicator with tooltip.
        """

        # noise indicator with toolip
        indicator_graph = dcc.Graph(
            id=COMPONENT_ID.mean_indicator,
            config={"displayModeBar": False},
            style={"visibility": "hidden"},
        )

        indicator_graph = dbc.Spinner(indicator_graph)

        indicator_tooltip = dbc.Tooltip(
            f"Average noise level in the past hour and relative change since the hour prior.",
            target=COMPONENT_ID.mean_indicator,
            placement="bottom",
            id=COMPONENT_ID.mean_indicator_tooltip,
        )

        return html.Div([indicator_graph, indicator_tooltip])

    def get_level_card(
        self,
    ) -> dbc.Card:

        card = self.get_card(
            title="Noise Level & Trend",
            body=dbc.CardBody(
                    [
                        html.Span(id=COMPONENT_ID.last_update_text),
                        html.Br(),
                        self._get_mean_indicator(),
                    ]
                ),
            logo="fa-arrow-trend-up",
            style={"height": "395px", "margin-bottom": "20px"}
        )

        return card

    def _get_location_start_date(self) -> date:
        """
        Find the first record date from location stats.
        """
        assert (
            self.data_manager.location_stats is not None
        ), "No location stats loaded, cannot get start date."
        start = self.data_manager.location_stats.loc[0, COLUMN.START]
        start = date(start.year, start.month, start.day)

        return start

    def _get_location_end_date(self) -> date:
        """
        Find last record date from location stats.
        """
        assert (
            self.data_manager.location_stats is not None
        ), "No location stats loaded, cannot get end date."
        end = self.data_manager.location_stats.loc[0, COLUMN.END]
        end = date(end.year, end.month, end.day)

        return end

    def _get_date_controls(
        self,
    ) -> html.Div:
        """
        Add component for controlling the date for the line graphs.
        """
        # set range for date picker
        min_date_allowed = self._get_location_start_date()
        max_date_allowed = self._get_location_end_date()

        # set default selection
        start_default = max_date_allowed - timedelta(days=7)
        end_default = max_date_allowed

        range_picker = dcc.DatePickerRange(
            id=COMPONENT_ID.date_picker,
            month_format="YYYY MMM",
            start_date=start_default,
            end_date=end_default,
            min_date_allowed=min_date_allowed,
            max_date_allowed=max_date_allowed,
        )

        return html.Div(range_picker)

    def _get_download_button(self) -> html.Div:
        """
        Get CSV download button.
        """
        button_component = html.Div(
            [
                html.Button(
                    "Download CSV",
                    id=COMPONENT_ID.download_button,
                    className="button",
                ),
                dcc.Download(id=COMPONENT_ID.download_csv),
            ]
        )
        return button_component


class CallbackManager:
    """
    Class that organizes and  initializes the Dash app callbacks on app start.
    """

    def __init__(self, data_manager: AppDataManager) -> None:
        self.data_manager = data_manager
        self.data_formatter = DataFormatter()

    
    def initialize_callbacks(self):
        def _update_fig_with_layout(relayout_data: dict, figure: dict) -> None:
            """
            Copy x-axis layout attributes into the figure.
            """
            if "xaxis.range[0]" in relayout_data:
                xmin = relayout_data["xaxis.range[0]"]
                xmax = relayout_data["xaxis.range[1]"]
                figure["layout"]["xaxis"]["range"] = [xmin, xmax]
                figure["layout"]["xaxis"]["autorange"] = False
            elif (
                "xaxis.autorange" in relayout_data
                and relayout_data["xaxis.autorange"] == True
            ):
                figure["layout"]["xaxis"]["autorange"] = True
            else:
                pass

        @callback(
            Output(COMPONENT_ID.download_csv, "data"),
            Input(COMPONENT_ID.download_button, "n_clicks"),
            prevent_initial_call=True,
        )
        def download_button_callback(n_clicks):
            # extract data
            noise_df = self.data_manager.location_noise[Granularity.raw]
            noise_df = (
                self.data_manager.data_formatter._enum_col_names_to_string(
                    noise_df
                )
            )

            # date as index
            noise_df = noise_df.set_index(COLUMN.TIMESTAMP.value)

            id = self.data_manager.device_id
            start = date_to_string(min(noise_df.index))
            end = date_to_string(max(noise_df.index))
            file_name = f"noise_data_ID{id}_{start}_to_{end}.csv"

            return dcc.send_data_frame(noise_df.to_csv, file_name)

        @callback(
            Output(COMPONENT_ID.hourly_data_store, "data"),
            Input(COMPONENT_ID.raw_data_store, "data"),
        )
        def aggregate_raw_to_hourly(raw_data: List[Dict[str, object]]) -> List[Dict[str, object]]:
            """
            Take the raw data and resample to hourly.
            """
            raw_df = self.data_formatter.store_to_dataframe(raw_data)

            # aggregate
            raw_df = raw_df.set_index(COLUMN.TIMESTAMP)
            hourly_df = raw_df.resample("1H").agg(
                {
                    COLUMN.MEAN: "mean",
                    COLUMN.MIN: "min",
                    COLUMN.MAX: "max"
                }
            )
            hourly_df = hourly_df.reset_index()

            self.data_manager.location_noise[Granularity.hourly] = hourly_df

            hourly_data = self.data_formatter.dataframe_to_store(hourly_df)

            return hourly_data
        
        @callback(
            Output(COMPONENT_ID.raw_data_store, "data"),
            Input(COMPONENT_ID.date_picker, "start_date"),
            Input(COMPONENT_ID.date_picker, "end_date"),
        )
        def load_data(start_date: date, end_date: date) -> List[Dict[str, object]]:
            """
            Load data based on date picker into client-side raw data store.
            """
            device_id = self.data_manager.device_id

            start_date = date.fromisoformat(start_date)
            end_date = date.fromisoformat(end_date)
            end_date += timedelta(days=1)
            
            self.data_manager.load_and_format_location_noise(
                location_id=device_id,
                granularity=Granularity.raw,
                start=start_date,
                end=end_date,
            )

            raw_data = self.data_manager.location_noise[Granularity.raw]
            raw_data = self.data_formatter.dataframe_to_store(raw_data)

            return raw_data
        
        @callback(
            Output(
                COMPONENT_ID.hourly_noise_line_graph,
                "figure",
                allow_duplicate=True,
            ),
            Output(COMPONENT_ID.hourly_noise_line_graph, "style"),
            Output(
                COMPONENT_ID.raw_noise_line_graph,
                "figure",
                allow_duplicate=True,
            ),
            Output(COMPONENT_ID.raw_noise_line_graph, "style"),
            Input(COMPONENT_ID.hourly_data_store, "data"),
            Input(COMPONENT_ID.raw_data_store, "data"),
            prevent_initial_call="initial_duplicate",
        )
        def update_line_charts(hourly_data: List[Dict[str, float]], raw_data: List[Dict[str, float]]):
            """
            Main callback responsible for loading data based on the date selector,
            updating the line charts and storing aggregate noise data.
            """

            raw_data = self.data_formatter.store_to_dataframe(raw_data)
            plotter = TimeseriesPlotter(raw_data)
            raw_line_fig = plotter.plot(bold_line=False)

            hourly_data = self.data_formatter.store_to_dataframe(hourly_data)
            plotter = TimeseriesPlotter(hourly_data)
            hourly_line_fig = plotter.plot(bold_line=True)

            return hourly_line_fig, {}, raw_line_fig, {}

        @callback(
            Output(COMPONENT_ID.last_update_text, "children"),
            Output(COMPONENT_ID.mean_indicator, "figure"),
            Output(COMPONENT_ID.mean_indicator, "style"),
            Input(COMPONENT_ID.hourly_data_store, "data"),
        )
        def update_trend_indicator(data):
            """
            The indicator component is updated whenever new hourly data is loaded into the store.
            Style needs to be cleared as it is set to invisible by default to avoid loading an empty chart.
            """
            data = pd.DataFrame(data)
            data = self.data_formatter._string_col_names_to_enum(data)

            plotter = MeanIndicatorPlotter(data)
            indicator_fig = plotter.plot()

            last_time = get_last_time(data)
            update_text = (html.H5([f"Recorded at {last_time}"]),)

            return update_text, indicator_fig, {}

        @callback(
            Output(COMPONENT_ID.hourly_noise_line_graph, "figure"),
            Output(COMPONENT_ID.raw_noise_line_graph, "figure"),
            Input(COMPONENT_ID.hourly_noise_line_graph, "relayoutData"),
            Input(COMPONENT_ID.raw_noise_line_graph, "relayoutData"),
            prevent_initial_call=True,
        )
        def update_zoom(hourly_relout, raw_relout):
            """
            Copy layout settings from one fig to other.
            """
            patched_raw = Patch()
            patched_hourly = Patch()

            if (
                dash.ctx.triggered_id == COMPONENT_ID.raw_noise_line_graph
                and isinstance(raw_relout, dict)
            ):
                _update_fig_with_layout(raw_relout, patched_hourly)

            if (
                dash.ctx.triggered_id == COMPONENT_ID.hourly_noise_line_graph
                and isinstance(hourly_relout, dict)
            ):
                _update_fig_with_layout(hourly_relout, patched_raw)

            return (patched_hourly, patched_raw)

        clientside_callback(
            """
            function(feature, n_clicks) {
                var base_url = window.location.href;
                console.log(feature)
                if (!feature.properties.cluster) {
                    var url = new URL("locations/".concat(feature.properties.id), base_url);
                    console.log(`Redirecting to ${url}`);
                    window.open(url, '_blank');
                }
            }
            """,
            Output(COMPONENT_ID.map_markers, "hideout"),
            Input(COMPONENT_ID.map_markers, "clickData"),
            Input(COMPONENT_ID.map_markers, "n_clicks"),
            prevent_initial_call=True,
        )
