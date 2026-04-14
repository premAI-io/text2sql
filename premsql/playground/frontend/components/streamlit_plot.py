from typing import Dict, Any
import pandas as pd
import streamlit as st
from premsql.logger import setup_console_logger
from premsql.agents.tools.plot.base import BasePlotTool
from premsql.security import safe_error_message

logger = setup_console_logger("[STREAMLIT-TOOL]")

class StreamlitPlotTool(BasePlotTool):
    def __init__(self):
        self.plot_functions = {
            "area": self._area_plot,
            "bar": self._bar_plot,
            "scatter": self._scatter_plot,
            "histogram": self._histogram_plot,
            "line": self._line_plot,
        }

    def run(self, data: pd.DataFrame, plot_config: Dict[str, str]) -> Any:
        try:
            self._validate_config(data, plot_config)

            plot_type = plot_config["plot_type"]
            x = plot_config["x"]
            y = plot_config["y"]

            st.markdown(f"**{plot_type.capitalize()} Plot: {x} vs {y}**")
            return self.plot_functions[plot_type](data, x, y)
        except Exception as exc:
            # Use safe error message (whitelist approach)
            safe_msg = safe_error_message(exc, debug_mode=False)
            logger.error(f"Plot error: {safe_msg}")
            st.error(safe_msg)
            return None

    def _validate_config(self, df: pd.DataFrame, plot_config: Dict[str, str]) -> None:
        required_keys = ["plot_type", "x", "y"]
        missing_keys = [key for key in required_keys if key not in plot_config]
        if missing_keys:
            raise ValueError(f"Missing required keys in plot_config: {', '.join(missing_keys)}")

        for key in ["x", "y"]:
            if key not in plot_config:
                raise ValueError(f"'{key}' is missing from plot_config")
            if not isinstance(plot_config[key], str):
                raise TypeError(f"plot_config['{key}'] should be a string, but got {type(plot_config[key])}")

        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"Expected df to be a pandas DataFrame, but got {type(df)}")

        if not hasattr(df, 'columns'):
            raise AttributeError(f"df does not have a 'columns' attribute. Type: {type(df)}")

        if plot_config["x"] not in df.columns:
            raise ValueError(f"Column '{plot_config['x']}' not found in DataFrame. Available columns: {', '.join(df.columns)}")

        if plot_config["y"] not in df.columns:
            raise ValueError(f"Column '{plot_config['y']}' not found in DataFrame. Available columns: {', '.join(df.columns)}")

        if plot_config["plot_type"] not in self.plot_functions:
            raise ValueError(f"Unsupported plot type: {plot_config['plot_type']}. Supported types: {', '.join(self.plot_functions.keys())}")

    def _area_plot(self, df: pd.DataFrame, x: str, y: str) -> Any:
        chart_data = df[[x, y]].set_index(x)
        return st.area_chart(chart_data)

    def _bar_plot(self, df: pd.DataFrame, x: str, y: str) -> Any:
        chart_data = df[[x, y]].set_index(x)
        return st.bar_chart(chart_data)

    def _scatter_plot(self, df: pd.DataFrame, x: str, y: str) -> Any:
        chart_data = df[[x, y]]
        return st.scatter_chart(chart_data, x=x, y=y)

    def _histogram_plot(self, df: pd.DataFrame, x: str, y: str) -> Any:
        # Streamlit doesn't have a built-in histogram function, so we'll use a bar chart
        hist_data = df[x].value_counts().sort_index()
        chart_data = pd.DataFrame({x: hist_data.index, 'count': hist_data.values})
        return st.bar_chart(chart_data.set_index(x))

    def _line_plot(self, df: pd.DataFrame, x: str, y: str) -> Any:
        chart_data = df[[x, y]].set_index(x)
        return st.line_chart(chart_data)
    
    def convert_plot_to_image(self, fig):
        pass 