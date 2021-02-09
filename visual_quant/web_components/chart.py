import logging
import dash_core_components as dcc
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import dash
import dash_bootstrap_components as dbc
import dash_html_components as html

import visual_quant.web_components.series as series
from visual_quant.web_components.component import Component


# callback names
CHART_DROPDOWN = "chart-dropdown"
CHART_GRAPH = "chart-graph"
CHART_NAME = "chart-name"

# provides a interactive chart using the dash graph and dropdown
# can hold multiple series
class Chart(Component):

    # constructors

    def __init__(self, app, name):
        # the path is always "Charts" from the json file
        super().__init__(app, name, "Charts")
        self.series = {}

        # graph callbacks

        app.callback(
            Output({"type": CHART_GRAPH, "uid": MATCH}, "figure"),  # charts figure
            Input({"type":.CHART_DROPDOWN, "uid": MATCH}, "value"),  # charts selected series
            State({"type": CHART_NAME, "uid": MATCH}, "className")  # chart name
        )(self.graph_dropdown)

    # constructor for directly adding series to the chart
    @classmethod
    def from_series(cls, app: dash.Dash, name: str, series: list):
        obj = cls(app, name)
        for s in series:
            obj.add_series(s)

        return obj

    # load the chart from a json dict
    @classmethod
    def from_json(cls, app: dash.Dash, chart_json: dict):
        logger = logging.getLogger(__name__)

        try:
            name = chart_json["Name"]
            series_json = chart_json["Series"]
        except KeyError as e:
            logger.error(f"Trying to load chart from json dict that has no name or series field\n{e}")
            return None

        # add the all series in the chart
        series = []
        for s in series_json:
            s = series_json[s]
            if Series.from_json(app, s) is not None:
                series.append(Series.from_json(app, s))

        return cls.from_series(app, name, series)

    @classmethod
    def from_save_file(cls, app: dash.Dash, save_json: dict, result_file_data: dict):
        return cls.from_json(app, result_file_data)

    # magic

    def __str__(self):
        # nice way to print chart information
        data_frames = ""
        for s in self.series:
            data_frames += str(self.series[s])
        return f"Chart: {self.name}\n{data_frames}"

    # properties

    @property
    def json(self) -> dict:
        json = {
            "type": "chart",
            "series": list(self.series.keys()),
            "name": self.name,
            "path": self.path
        }

        return json

    # methods

    @staticmethod
    def layout(name):
        # TODO don't hard code colors, base them on the selected theme
        layout = {
            "paper_bgcolor": "rgba(0, 0, 0, 0)",
            "plot_bgcolor": "rgba(0, 0, 0, 0)",
            "title.text": name,
            "title.font.color": "rgba(220, 220, 220, 255)",
            "legend.font.color": "rgba(220, 220, 220, 255)",
        }

        return layout

    def graph_dropdown(self, values: list, chart_name: str):
        fig = go.Figure(layout=Chart.layout(chart_name))
        if values is not None:
            for series_name in values:
                # TODO use the json_loader
                s = series.Series.from_json(self.app, self.data["Charts"][chart_name]["Series"][series_name])
                fig.add_trace(s.get_figure())
        return fig

    def add_series(self, new_series: series.Series):
        if new_series.name in self.series:
            self.logger.warning(f"The series named {new_series.name} already exists in the chart {self.name}")
        self.series[new_series.name] = new_series

    def join(self, other: "Chart"):
        self.series = {**self.series, **other.series}

    # get options in format for dropdown
    def get_options(self):
        options = []
        for s in self.series:
            options.append({"label": s, "value": s})
        self.logger.debug(f"get options. options are {options}")
        return options

    # TODO
    # callback function for dropdown
    # build figure based on the values from the dropdown
    def create_figures(self, series_names: list):
        self.logger.debug(f"creating figures with series {list(self.series.keys())}")
        fig = go.Figure(layout=self.layout(self.name))
        for name in series_names:
            s = self.series[name]
            fig.add_trace(s.get_figure())
        return fig

    def get_html(self):

        drop_down = dcc.Dropdown(id={"type": CHART_DROPDOWN, "uid": self.uid},
                                 options=self.get_options(),
                                 value=list(self.series.keys()),
                                 multi=True,
                                 style={"background-color": "rgba(0, 0, 0, 0)", "color": "rgba(30, 30, 30, 255)"})

        graph = dcc.Graph({"type": CHART_GRAPH, "uid": self.uid})

        self.logger.debug(f"getting html for graph {self.name}")

        return dbc.Col(
            dbc.Card(
                [
                    drop_down,
                    graph
                ]
            ),
            style={"padding": "10px", "min-width": "900px"},
            className=self.name,
            id={"type": CHART_NAME, "uid": self.uid}
        )