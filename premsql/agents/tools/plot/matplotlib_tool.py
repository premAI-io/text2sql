import io
from typing import Callable, Dict

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server mode
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from PIL import Image

from premsql.logger import setup_console_logger
from premsql.agents.tools.plot.base import BasePlotTool

logger = setup_console_logger("[MATPLOTLIB-TOOL]")


class SimpleMatplotlibTool(BasePlotTool):
    def __init__(self):
        self.plot_functions: Dict[
            str, Callable[[pd.DataFrame, str, str, Axes], None]
        ] = {
            "area": self._area_plot,
            "bar": self._bar_plot,
            "scatter": self._scatter_plot,
            "histogram": self._histogram_plot,
            "line": self._line_plot,
        }

    def run(self, data: pd.DataFrame, plot_config: Dict[str, str]) -> Figure:
        try:
            self._validate_config(data, plot_config)

            plot_type = plot_config["plot_type"]
            x = plot_config["x"]
            y = plot_config["y"]

            fig, ax = plt.subplots(figsize=(10, 6))
            self.plot_functions[plot_type](data, x, y, ax)

            plt.title(f"{plot_type.capitalize()} Plot: {x} vs {y}")
            plt.xlabel(x)
            plt.ylabel(y)
            plt.tight_layout()

            return fig
        except Exception as e:
            logger.error(f"Error creating plot: {str(e)}")
            return plt.figure()  # Return an empty figure on error

    def _validate_config(self, df: pd.DataFrame, plot_config: Dict[str, str]) -> None:
        required_keys = ["plot_type", "x", "y"]
        missing_keys = [key for key in required_keys if key not in plot_config]
        if missing_keys:
            raise ValueError(
                f"Missing required keys in plot_config: {', '.join(missing_keys)}"
            )

        if plot_config["plot_type"] not in self.plot_functions:
            raise ValueError(f"Unsupported plot type: {plot_config['plot_type']}")

        if plot_config["x"] not in df.columns:
            raise ValueError(f"Column '{plot_config['x']}' not found in DataFrame")

        if plot_config["plot_type"] == "histogram":
            return

        if plot_config["y"] not in df.columns:
            raise ValueError(f"Column '{plot_config['y']}' not found in DataFrame")

    def _area_plot(self, df: pd.DataFrame, x: str, y: str, ax: Axes) -> None:
        ax.fill_between(df[x], df[y])

    def _bar_plot(self, df: pd.DataFrame, x: str, y: str, ax: Axes) -> None:
        ax.bar(df[x], df[y])

    def _scatter_plot(self, df: pd.DataFrame, x: str, y: str, ax: Axes) -> None:
        ax.scatter(df[x], df[y])

    def _histogram_plot(self, df: pd.DataFrame, x: str, y: str, ax: Axes) -> None:
        ax.hist(df[x], bins=20)

    def _line_plot(self, df: pd.DataFrame, x: str, y: str, ax: Axes) -> None:
        ax.plot(df[x], df[y])

    def convert_plot_to_image(self, fig: Figure) -> Image.Image:
        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        return Image.open(buf)
