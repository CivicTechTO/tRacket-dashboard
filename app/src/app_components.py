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

<<<<<<< HEAD
                Developed & maintained by the CivicTech TO community using [Plotly Dash](https://dash.plotly.com/) and hosted on [Heroku](https://www.heroku.com/). 
                
                Source: [Github](https://github.com/danieltsoukup/noise-dashboard)
                """
        )
        about_body = html.Div([about_intro, quote, about_outro])

        about_modal = html.Div(
            [
                dbc.Button("About", id="open", color="primary", n_clicks=0),
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle("About")),
                        dbc.ModalBody(about_body),
                    ],
                    id="modal",
                    is_open=False,
                ),
            ]
        )
        cls.navbar = dbc.NavbarSimple(
            children=[about_modal],
            brand=html.Span(
                [
                    "Toronto Noise Monitor ",
                    html.I(className="fa-solid fa-tower-broadcast"),
                ]
            ),
            color="primary",
            dark=True,
            fixed="top",
        )


class InputManager(AbstractAppManager):
    """
    Component manager for user inputs.
    """

    device_id_dropdown: dcc.Dropdown = None
    heatmap_toggle = None
    config = load_config()

    @classmethod
    def initialize(cls, app_data_manager: AppDataManager) -> None:
        cls._set_app_data_manager(app_data_manager)
        cls._initialize_device_id_dropdown()
        cls._initialize_heatmap_toggle()

    @classmethod
    def _initialize_device_id_dropdown(cls) -> None:
        """
        Setup dropdown for device IDs marking which is active.
        """
        active_icon = cls.config["components.inputs"]["active_icon"]
        inactive_icon = cls.config["components.inputs"]["inactive_icon"]

        options = [
            {"label": active_icon + " " + value, "value": value}
            for value in cls.app_data_manager.active_ids
        ]
        options += [
            {"label": inactive_icon + " " + value, "value": value}
            for value in cls.app_data_manager.inactive_ids
        ]

        cls.device_id_dropdown = dbc.Select(
            options,
            options[0],
            id=COMPONENT_ID.device_id_input,
        )

    @classmethod
    def _initialize_heatmap_toggle(cls) -> None:
        cls.heatmap_toggle = dbc.Switch(
            id=COMPONENT_ID.heatmap_toggle,
            label="Toggle Between Min & Max",
            value=False,
        )


class GraphManager(AbstractAppManager):
    """
    Class to collect and initialize the graph components for the app.
    """

    _config = load_config()
    _boostrap_template_name = _config["bootstrap"]["theme"]

    # system-level indicators
    system_count_indicator: dcc.Graph = None
    system_avg_indicator: dcc.Graph = None
    system_outlier_indicator: dcc.Graph = None

    # device level charts
    noise_line_graph: dcc.Graph = None
    heatmap: dcc.Graph = None
    histogram: dcc.Graph = None
    day_time_indicator: dcc.Graph = None
    evening_time_indicator: dcc.Graph = None
    night_time_indicator: dcc.Graph = None
    system_map: dcc.Graph = None
    device_map: dcc.Graph = None

    @classmethod
    def initialize(cls, app_data_manager: AppDataManager) -> None:
        """
        Main call to setup all graph components for the app.
        """
        cls._set_app_data_manager(app_data_manager)

        # system level
        cls._setup_system_indicators()
        cls._setup_system_map()

        # device level
        cls._setup_noise_line_graph()
        cls._setup_heatmap_graph()
        cls._setup_histogram()
        cls._setup_time_of_day_indicators()
        cls._setup_device_map()

    @classmethod
    def _setup_system_map(cls) -> None:
        plotter = MapPlotter(cls.app_data_manager.device_locations, bootstrap_template=cls._boostrap_template_name)
        fig = plotter.plot()
        cls.system_map = dcc.Graph(
            figure=fig, 
            id=COMPONENT_ID.system_map,
            config={"displayModeBar": False}
        )

    @classmethod
    def _setup_device_map(cls) -> None:
        cls.device_map = dcc.Graph(
            id=COMPONENT_ID.device_map,
            config={"displayModeBar": False}
        )


    @classmethod
    def _setup_histogram(cls) -> None:
        cls.histogram = dcc.Graph(
            id=COMPONENT_ID.histogram, config={"displayModeBar": False}
        )

    @classmethod
    def _setup_heatmap_graph(cls) -> None:
        cls.heatmap = dcc.Graph(
            id=COMPONENT_ID.heatmap, config={"displayModeBar": False}
        )

    @classmethod
    def _setup_noise_line_graph(cls) -> None:
        cls.noise_line_graph = dcc.Graph(
            id=COMPONENT_ID.noise_line_graph, config={"displayModeBar": False}
        )

    @classmethod
    def _setup_system_indicators(cls) -> None:
        """
        Initialize system indicator graphs.
        """
        cls._setup_device_count_indicator()
        cls._setup_system_min_indicator()
        cls._setup_system_outlier_indicator()

    @classmethod
    def _setup_device_count_indicator(cls) -> None:
        indicator_plotter = DeviceCountIndicatorPlotter(
            cls.app_data_manager.system_stats_df
        )
        system_count_fig = indicator_plotter.plot()
        cls.system_count_indicator = html.Div(
            [
                html.Div(
                    [
                        dcc.Graph(
                            figure=system_count_fig,
                            style={"height": "40vh"},
                            config={"displayModeBar": False},
                        )
                    ],
                    id=COMPONENT_ID.count_indicator,
                ),
                dbc.Tooltip(
                    "A device is active if it sent data to our server in the past 7 days. The small value below indicates the week-over-week difference.",
                    target=COMPONENT_ID.count_indicator,
                    id=COMPONENT_ID.count_indicator_tooltip,
                    placement="bottom",
                ),
            ]
        )

    @classmethod
    def _setup_system_min_indicator(cls) -> None:
        indicator_plotter = MinAverageIndicatorPlotter(
            cls.app_data_manager.system_stats_df
        )
        system_min_fig = indicator_plotter.plot()
        cls.system_avg_indicator = html.Div(
            [
                html.Div(
                    [
                        dcc.Graph(
                            figure=system_min_fig,
                            style={"height": "40vh"},
                            config={"displayModeBar": False},
                            clear_on_unhover=True,
                        )
                    ],
                    id=COMPONENT_ID.avg_indicator,
                ),
                dbc.Tooltip(
                    "This is the system-wide average of recorded minimum noise levels for the past 7 days. The small value below indicates the week-over-week difference.",
                    id=COMPONENT_ID.avg_indicator_tooltip,
                    target=COMPONENT_ID.avg_indicator,
                    placement="bottom",
                ),
            ]
        )

    @classmethod
    def _setup_system_outlier_indicator(cls) -> None:
        indicator_plotter = OutlierIndicatorPlotter(
            cls.app_data_manager.system_stats_df
        )
        system_outlier_fig = indicator_plotter.plot()
        cls.system_outlier_indicator = html.Div(
            [
                html.Div(
                    [
                        dcc.Graph(
                            figure=system_outlier_fig,
                            style={"height": "40vh"},
                            config={"displayModeBar": False},
                        )
                    ],
                    id=COMPONENT_ID.outlier_indicator,
                ),
                dbc.Tooltip(
                    f"This is the number of recordings above {cls._config['constants']['noise_threshold']} dBA in the past 7 days. The small value below indicates the week-over-week difference.",
                    id=COMPONENT_ID.outlier_indicator_tooltip,
                    target=COMPONENT_ID.outlier_indicator,
                    placement="bottom",
                ),
            ]
        )

    @classmethod
    def _create_indicator_component(
        cls,
        graph_id: COMPONENT_ID,
        graph_div_id: COMPONENT_ID,
        tooltip_id: COMPONENT_ID,
        figure: Figure = None,
        tooltip_text: str = ""
        ) -> html.Div:
        """
        Create one time of day indicator component with given divs.
        """

        component = html.Div(
            [
                html.Div(
                    [
                        dcc.Graph(
                            style={"height": "40vh"},
                            config={"displayModeBar": False},
                            id=graph_id
                        ),
                    ],
                    id=graph_div_id,
                ),
                dbc.Tooltip(
                    tooltip_text,
                    id=tooltip_id,
                    target=graph_div_id,
                    placement="bottom",
                ),
            ]
        )

        return component


    @classmethod
    def _setup_time_of_day_indicators(cls) -> None:
        cls.evening_time_indicator = cls._create_indicator_component(
            graph_id=COMPONENT_ID.evening_indicator,
            graph_div_id=COMPONENT_ID.evening_indicator_div,
            tooltip_id=COMPONENT_ID.evening_indicator_tooltip,
            tooltip_text=f"Average ambient noise level for the selected device during evening time. The small value below indicates the week-over-week difference."
        )

        cls.day_time_indicator = cls._create_indicator_component(
            graph_id=COMPONENT_ID.day_indicator,
            graph_div_id=COMPONENT_ID.day_indicator_div,
            tooltip_id=COMPONENT_ID.day_indicator_tooltip,
            tooltip_text=f"Average ambient noise level for the selected device during day time. The small value below indicates the week-over-week difference."
        )

        cls.night_time_indicator = cls._create_indicator_component(
            graph_id=COMPONENT_ID.night_indicator,
            graph_div_id=COMPONENT_ID.night_indicator_div,
            tooltip_id=COMPONENT_ID.night_indicator_tooltip,
            tooltip_text=f"Average ambient noise level for the selected device during night time. The small value below indicates the week-over-week difference."
        )
        

class CallbackManager(AbstractAppManager):
    """
    Class that organizes and  initializes the Dash app callbacks on app start.
    """

    _config = load_config()
    _boostrap_template_name = _config["bootstrap"]["theme"]

    @classmethod
    def _initialize_card_callbacks(cls) -> None:
        """
        Initialize callbacks updating cards.
        """
        @callback(
            Output(COMPONENT_ID.summary_card_text, "children"),
            Input(COMPONENT_ID.device_stats_store, "data"),
        )
        def update_card_text(stats: List[dict]) -> str:
            """
            Insert device id into the card.
            """
            stats_dict = stats[0]

            count = stats_dict[COLUMN.COUNT.value]

            date_format = "%Y-%m-%d"
            min_date = stats_dict[COLUMN.MINDATE.value]
            formatted_min_date = pd.to_datetime(min_date).strftime(date_format)

            max_date = stats_dict[COLUMN.MAXDATE.value]
            formatted_max_date = pd.to_datetime(max_date).strftime(date_format)

            max_noise = stats_dict[COLUMN.MAXNOISE.value]

            text = (
                f"This device has recorder a total of {count} measurements between "
                f" {formatted_min_date} and {formatted_max_date}. "
                f" The loudest measurement recorded to date was at {max_noise} dBA."
=======
            selected_device_marker = dl.Circle(
                center=[lat, lon],
                radius=self.config["map"]["radius-meter"],
                fillColor=self.config["map"]["marker_color_highlight"],
                color=self.config["map"]["marker_color_highlight"],
>>>>>>> api_redesign
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

    def get_map(self, device_id: str = None) -> dl.Map:
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
            style={"height": "100vh"},
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
