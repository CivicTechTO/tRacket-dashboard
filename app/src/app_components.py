from dash import callback, Input, Output, dcc, html, no_update
import dash_bootstrap_components as dbc
from typing import List, Dict, Any, Optional
from src.data_loading import AppDataManager
from src.utils import COLUMN, HEATMAP_VALUE, load_config
from enum import StrEnum, auto
from abc import abstractclassmethod
import pandas as pd
from src.plotting import (
    TimeseriesPlotter,
    HeatmapPlotter,
    HistogramPlotter,
    OutlierIndicatorPlotter,
    MinAverageIndicatorPlotter,
    DeviceCountIndicatorPlotter,
)
from plotly.graph_objects import Figure


class COMPONENT_ID(StrEnum):
    """
    Component IDs for the app.
    """

    # graphs
    histogram = auto()
    noise_line_graph = auto()
    heatmap = auto()
    count_indicator = auto()
    count_indicator_tooltip = auto()
    avg_indicator = auto()
    avg_indicator_tooltip = auto()
    outlier_indicator = auto()
    outlier_indicator_tooltip = auto()

    # inputs
    device_id_input = auto()
    heatmap_toggle = auto()

    # markdowns
    summary_card_header = auto()
    summary_card_text = auto()

    # store
    device_data_store = auto()
    device_stats_store = auto()
    hourly_device_data_store = auto()


class AbstractAppManager(object):
    """
    Base class for managing app components.
    """

    app_data_manager: AppDataManager = None

    @classmethod
    def _set_app_data_manager(cls, app_data_manager: AppDataManager) -> None:
        cls.app_data_manager = app_data_manager

    @abstractclassmethod
    def initialize(
        cls, app_data_manager: Optional[AppDataManager] = None
    ) -> None:
        if app_data_manager:
            cls._set_app_data_manager(app_data_manager)
        pass


class DataStoreManager(AbstractAppManager):
    """
    Class for initializing the clien-side data stores for re-use.
    """

    device_data_store: dcc.Store = None
    device_stats_store: dcc.Store = None
    hourly_device_data_store: dcc.Store = None

    @classmethod
    def initialize(cls) -> None:
        cls.device_data_store = dcc.Store(id=COMPONENT_ID.device_data_store)
        cls.device_stats_store = dcc.Store(id=COMPONENT_ID.device_stats_store)
        cls.hourly_device_data_store = dcc.Store(
            id=COMPONENT_ID.hourly_device_data_store
        )


class MarkdownManager(AbstractAppManager):
    """
    Class for handling text components in the app.
    """

    summary_card: dbc.Card = None
    intro_markdown: dcc.Markdown = None
    system_stats_markdown: dcc.Markdown = None
    heatmap_markdown: dcc.Markdown = None

    style = {"textAlign": "left", "margin-left": "30px"}

    @classmethod
    def initialize(cls, app_data_manager: AppDataManager) -> None:
        """
        Main call to initialize all app markdowns.
        """
        cls._set_app_data_manager(app_data_manager)
        cls._initialize_summary_card()
        cls._initialize_intro_mardown()
        cls._initialize_system_markdown()
        cls._initialize_heatmap_markdown()

    @classmethod
    def _initialize_system_markdown(cls) -> None:
        text = "The summary statistics are calculated by aggregating data for the past 7 days and comparing to the prior week."
        cls.system_stats_markdown = dcc.Markdown(text, style=cls.style)

    @classmethod
    def _initialize_intro_mardown(cls) -> None:
        """
        Intro text after the title.
        """
        text = """
                Environmental noise, especially in urban settings, is a [known public health concern](https://www.toronto.ca/wp-content/uploads/2017/11/8f98-tph-How-Loud-is-Too-Loud-Health-Impacts-Environmental-Noise.pdf):
                >
                > _"The growing body of evidence indicates that exposure to excessive environmental noise does not only impact quality of life and cause hearing loss but also has other health impacts, such as cardiovascular effects, cognitive impacts, sleep disturbance and mental health effects."_
                >
                Our application presents a real-time, interactive visual interface to a system of IoT sound meters deployed in the city of Toronto, Ontario, to better understand the ambient sound levels as well as extreme noise events local communities experience day to day.
                """

        cls.intro_markdown = dcc.Markdown(text, style=cls.style)

    @classmethod
    def _initialize_summary_card(cls) -> None:
        cls.summary_card = dbc.Card(
            [
                dbc.CardHeader(id=COMPONENT_ID.summary_card_header),
                dbc.CardBody(
                    [
                        html.H4("Summary", className="card-title"),
                        html.P(
                            id=COMPONENT_ID.summary_card_text,
                            className="card-text",
                        ),
                    ]
                ),
            ],
            style={"width": "18rem"},
        )

    @classmethod
    def _initialize_heatmap_markdown(cls) -> None:
        text = f"To select a different week for the line graph, click the heatmap below."
        cls.heatmap_markdown = dcc.Markdown(text, style=cls.style)


class InputManager(AbstractAppManager):
    """
    Component manager for user inputs.
    """

    device_id_dropdown: dcc.Dropdown = None
    heatmap_toggle = None

    @classmethod
    def initialize(cls, app_data_manager: AppDataManager) -> None:
        cls._set_app_data_manager(app_data_manager)
        cls._initialize_device_id_dropdown()
        cls._initialize_heatmap_toggle()

    @classmethod
    def _initialize_device_id_dropdown(cls) -> None:
        cls.device_id_dropdown = dbc.Select(
            cls.app_data_manager.unique_ids,
            cls.app_data_manager.unique_ids[0],
            id=COMPONENT_ID.device_id_input,
        )

    @classmethod
    def _initialize_heatmap_toggle(cls) -> None:
        cls.heatmap_toggle = dbc.Switch(
            id=COMPONENT_ID.heatmap_toggle,
            label="Toggle Heatmap Min/Max",
            value=False,
        )


class GraphManager(AbstractAppManager):
    """
    Class to collect and initialize the graph components for the app.
    """

    _config = load_config()

    # system-level indicators
    system_count_indicator: dcc.Graph = None
    system_avg_indicator: dcc.Graph = None
    system_outlier_indicator: dcc.Graph = None

    # device level charts
    noise_line_graph: dcc.Graph = None
    heatmap: dcc.Graph = None
    histogram: dcc.Graph = None

    @classmethod
    def initialize(cls, app_data_manager: AppDataManager) -> None:
        """
        Main call to setup all graph components for the app.
        """
        cls._set_app_data_manager(app_data_manager)

        # system level
        cls._setup_system_indicators()

        # device level
        cls._setup_noise_line_graph()
        cls._setup_heatmap_graph()
        cls._setup_histogram()

    @classmethod
    def _setup_histogram(cls) -> None:
        cls.histogram = dcc.Graph(id=COMPONENT_ID.histogram)

    @classmethod
    def _setup_heatmap_graph(cls) -> None:
        cls.heatmap = dcc.Graph(id=COMPONENT_ID.heatmap)

    @classmethod
    def _setup_noise_line_graph(cls) -> None:
        cls.noise_line_graph = dcc.Graph(id=COMPONENT_ID.noise_line_graph)

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


class CallbackManager(AbstractAppManager):
    """
    Class that organizes and  initializes the Dash app callbacks on app start.
    """

    _config = load_config()

    @classmethod
    def initialize(cls, app_data_manager: AppDataManager) -> None:
        cls._set_app_data_manager(app_data_manager)
        ### CARD CALLBACKS ###

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
            )

            return text

        @callback(
            Output(COMPONENT_ID.summary_card_header, "children"),
            Input(COMPONENT_ID.device_id_input, "value"),
        )
        def update_card_header(device_id: str) -> str:
            """
            Insert device id into the card.
            """

            return f"Device ID: {device_id}"

        ### DATA CALLBACKS ###

        @callback(
            Output(COMPONENT_ID.device_stats_store, "data"),
            Input(COMPONENT_ID.device_id_input, "value"),
        )
        def load_device_stats(device_id: str) -> List[Dict[str, Any]]:
            """
            Load the data from the API.
            """
            raw_stats = cls.app_data_manager.load_device_stats(
                device_id=device_id
            )

            return raw_stats

        @callback(
            Output(COMPONENT_ID.hourly_device_data_store, "data"),
            Input(COMPONENT_ID.device_id_input, "value"),
        )
        def load_hourly_data(device_id: str) -> List[Dict[str, Any]]:
            """
            Load the data from the API.
            """
            raw_hourly_data = cls.app_data_manager.load_hourly_data(
                device_id=device_id
            )

            return raw_hourly_data

        @callback(
            Output(COMPONENT_ID.device_data_store, "data"),
            Input(COMPONENT_ID.device_id_input, "value"),
            Input(COMPONENT_ID.device_stats_store, "data"),
            Input(COMPONENT_ID.heatmap, "clickData"),
        )
        def load_data(
            device_id: str, stats: List[dict], clickData: Dict
        ) -> List[Dict[str, Any]]:
            """
            Load the data from the API.
            """

            date_format = "%Y-%m-%d"
            if clickData:
                # user selects end date
                date_string = clickData["points"][0]["x"]
                end_date = pd.Timestamp(date_string).strftime(date_format)

            else:
                # last recorded date used as end
                stats_dict = stats[0]
                end_date = stats_dict[COLUMN.MAXDATE.value]
                end_date = pd.to_datetime(end_date).strftime(date_format)

            # look back 7 days
            start_date = pd.to_datetime(end_date) - pd.Timedelta(days=7)
            start_date = start_date.strftime(date_format)

            # load data from API
            raw_device_data = cls.app_data_manager.load_noise_data(
                device_id=device_id, end_date=end_date, start_date=start_date
            )

            return raw_device_data

        ### PLOT CALLBACKS ###

        @callback(
            Output(COMPONENT_ID.noise_line_graph, "figure"),
            Input(COMPONENT_ID.device_data_store, "data"),
        )
        def update_noise_level_fig(data: List[Dict[str, Any]]) -> Figure:
            """
            Filter the line for a single device id.
            """
            df = cls.app_data_manager.data_formatter.process_records_to_dataframe(
                data
            )

            timeseries_plotter = TimeseriesPlotter(df)

            return timeseries_plotter.plot()

        @callback(
            Output(COMPONENT_ID.histogram, "figure"),
            Input(COMPONENT_ID.device_data_store, "data"),
        )
        def update_histogram(data: List[Dict[str, Any]]) -> Figure:
            """
            Histogram of min/max distribution.
            """
            df = cls.app_data_manager.data_formatter.process_records_to_dataframe(
                data
            )

            hist_plotter = HistogramPlotter(df)

            return hist_plotter.plot()

        @callback(
            Output(COMPONENT_ID.heatmap, "figure"),
            Input(COMPONENT_ID.hourly_device_data_store, "data"),
            Input(COMPONENT_ID.heatmap_toggle, "value"),
        )
        def update_heatmap(
            data: List[Dict[str, Any]], max_toggle: bool
        ) -> Figure:
            df = cls.app_data_manager.data_formatter.process_records_to_dataframe(
                data
            )
            heatmap_plotter = HeatmapPlotter(df)

            if max_toggle:
                title = (
                    "Hourly Highest Measures - click to filter for the week!"
                )
                pivot_value = HEATMAP_VALUE.MAX
            else:
                title = "Hourly Ambient Noise - click to filter for the week!"
                pivot_value = HEATMAP_VALUE.MIN

            return heatmap_plotter.plot(pivot_value=pivot_value, title=title)
