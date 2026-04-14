from datetime import datetime
from typing import Dict, Literal, Optional

import pandas as pd
from pydantic import BaseModel, Field

from premsql.logger import setup_console_logger

logger = setup_console_logger("[BASE-MODELS]")


class BaseWorkerOutput(BaseModel):
    """Base model for worker outputs with common fields."""

    question: str
    error_from_model: Optional[str] = None
    additional_input: Optional[Dict] = Field(
        default=None, description="Additional input data"
    )


class Text2SQLWorkerOutput(BaseWorkerOutput):
    """Output model for Text2SQL worker."""

    db_connection_uri: str
    sql_string: str
    sql_reasoning: Optional[str] = None
    input_dataframe: Optional[Dict] = None
    output_dataframe: Optional[Dict] = None

    def show_output_dataframe(self) -> pd.DataFrame:
        if self.output_dataframe:
            return pd.DataFrame(
                self.output_dataframe["data"], columns=self.output_dataframe["columns"]
            )
        return pd.DataFrame()


class AnalyserWorkerOutput(BaseWorkerOutput):
    """Output model for Analyser worker."""

    analysis: str
    input_dataframe: Optional[Dict] = None
    analysis_reasoning: Optional[str] = None


class ChartPlotWorkerOutput(BaseWorkerOutput):
    """Output model for ChartPlot worker."""

    input_dataframe: Optional[Dict] = None
    plot_config: Optional[Dict] = None
    image_plot: Optional[str] = None
    plot_reasoning: Optional[str] = None
    output_dataframe: Optional[Dict] = None


class RouterWorkerOutput(BaseWorkerOutput):
    """Output model for Router worker."""

    route_to: Literal["followup", "plot", "analyse", "query"]
    input_dataframe: Optional[Dict] = None
    decision_reasoning: Optional[str] = None


# This is a more of a custom worker
class FollowupWorkerOutput(BaseWorkerOutput):
    """Output model for Followup worker."""

    route_taken: Literal["followup", "plot", "analyse", "query"]
    suggestion: str
    alternative_route: Optional[Literal["followup", "plot", "analyse", "query"]] = None


class ExitWorkerOutput(BaseModel):
    """Output model for Exit worker, combining results from all workers."""

    session_name: str
    question: str
    db_connection_uri: str
    route_taken: Literal["plot", "analyse", "query", "followup"]

    # Text2SQL fields
    sql_string: Optional[str] = None
    sql_reasoning: Optional[str] = None
    sql_input_dataframe: Optional[Dict] = None
    sql_output_dataframe: Optional[Dict] = None
    error_from_sql_worker: Optional[str] = None

    # Analysis worker fields
    analysis: Optional[str] = None
    analysis_reasoning: Optional[str] = None
    analysis_input_dataframe: Optional[Dict] = None
    error_from_analysis_worker: Optional[str] = None

    # Plot Worker fields
    plot_config: Optional[Dict] = None
    plot_input_dataframe: Optional[Dict] = None
    plot_output_dataframe: Optional[Dict] = None
    image_to_plot: Optional[str] = None
    plot_reasoning: Optional[str] = None
    error_from_plot_worker: Optional[str] = None

    # Followup Worker fields
    followup_route_to_take: Optional[
        Literal["plot", "analyse", "query", "followup"]
    ] = None
    followup_suggestion: Optional[str] = None
    error_from_followup_worker: Optional[str] = None

    # Additional input
    additional_input: Optional[Dict] = Field(
        default=None, description="Additional input data"
    )

    def show_output_dataframe(
        self,
    ) -> pd.DataFrame:
        dataframe = None
        if self.route_taken == "query":
            dataframe = self.sql_output_dataframe
        elif self.route_taken == "plot":
            dataframe = self.plot_output_dataframe
        elif self.route_taken == "analyse":
            dataframe = self.analysis_input_dataframe

        if dataframe:
            return pd.DataFrame(dataframe["data"], columns=dataframe["columns"])
        return pd.DataFrame()


class AgentOutput(BaseModel):
    """Final output model for the entire pipeline."""

    session_name: str
    question: str
    db_connection_uri: Optional[str] = None
    route_taken: Literal["plot", "analyse", "query", "followup"]
    input_dataframe: Optional[Dict] = None
    output_dataframe: Optional[Dict] = None
    sql_string: Optional[str] = None
    analysis: Optional[str] = None
    reasoning: Optional[str] = None
    plot_config: Optional[Dict] = None
    image_to_plot: Optional[str] = None
    followup_route: Optional[Literal["plot", "analyse", "query", "followup"]] = None
    followup_suggestion: Optional[str] = None
    error_from_pipeline: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

    def show_output_dataframe(
        self,
    ) -> pd.DataFrame:
        dataframe = None
        if self.route_taken == "query":
            dataframe = self.sql_output_dataframe
        elif self.route_taken == "plot":
            dataframe = self.plot_output_dataframe
        elif self.route_taken == "analyse":
            dataframe = self.analysis_input_dataframe

        if dataframe:
            return pd.DataFrame(dataframe["data"], columns=dataframe["columns"])
        return pd.DataFrame()
