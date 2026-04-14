from abc import ABC, abstractmethod
from typing import Optional, Union

import pandas as pd

from premsql.executors.base import BaseExecutor
from premsql.executors.from_langchain import SQLDatabase
from premsql.generators.base import Text2SQLGeneratorBase
from premsql.logger import setup_console_logger
from premsql.agents.memory import AgentInteractionMemory
from premsql.agents.models import (
    AgentOutput,
    AnalyserWorkerOutput,
    ChartPlotWorkerOutput,
    ExitWorkerOutput,
    RouterWorkerOutput,
    Text2SQLWorkerOutput,
)

logger = setup_console_logger("[PIPELINE-BASE]")


# If someone wants to make a new worker class
class WorkerBase(ABC):
    @abstractmethod
    def run(self):
        return NotImplementedError()


class AnalysisWorkerBase(ABC):
    @abstractmethod
    def run(
        self, question: str, input_dataframe: Optional[pd.DataFrame] = None
    ) -> AnalyserWorkerOutput:
        raise NotImplementedError


class ChartPlotWorkerBase(ABC):
    @abstractmethod
    def run(
        self, question: str, input_dataframe: Optional[pd.DataFrame] = None
    ) -> ChartPlotWorkerOutput:
        raise NotImplementedError


class RouterWorkerBase(ABC):
    @abstractmethod
    def run(
        self, question: str, input_dataframe: Optional[pd.DataFrame] = None
    ) -> RouterWorkerOutput:
        raise NotImplementedError


class Text2SQLWorkerBase(ABC):
    def __init__(
        self,
        db_connection_uri: str,
        generator: Text2SQLGeneratorBase,
        executor: BaseExecutor,
        include_tables: Optional[str] = None,
        exclude_tables: Optional[str] = None,
    ) -> None:

        self.generator, self.executor = generator, executor
        self.db_connection_uri = db_connection_uri
        self.db = self.initialize_database(
            db_connection_uri=db_connection_uri,
            include_tables=include_tables,
            exclude_tables=exclude_tables,
        )

    @abstractmethod
    def run(self, question: str, **kwargs) -> Text2SQLWorkerOutput:
        raise NotImplementedError

    def initialize_database(
        self,
        db_connection_uri: str,
        include_tables: Optional[list] = None,
        exclude_tables: Optional[list] = None,
    ) -> SQLDatabase:
        """This method should return a db object

        To customise this method you make a different db object but
        it should have similar methods and behaviour like
        langchain SQLDatbase. You can find the implementation of SQLDatabase
        here: https://api.python.langchain.com/en/latest/_modules/langchain_community/utilities/sql_database.html#SQLDatabase
        """
        try:
            return SQLDatabase.from_uri(
                database_uri=db_connection_uri,
                sample_rows_in_table_info=0,
                ignore_tables=exclude_tables,
                include_tables=include_tables
            )
        except Exception as e:
            logger.error(f"Error loading the database: {e}")
            raise RuntimeError(f"Error loading the database: {e}")


class AgentBase(ABC):
    def __init__(
        self,
        session_name: str,
        db_connection_uri: str,
        session_db_path: Optional[str] = None,
        route_worker_kwargs: Optional[dict] = None,
    ) -> None:
        self.session_name, self.db_connection_uri = session_name, db_connection_uri
        self.history = AgentInteractionMemory(
            session_name=session_name, db_path=session_db_path
        )
        self.session_db_path = self.history.db_path
        self.route_worker_kwargs = route_worker_kwargs

    @abstractmethod
    def run(
        self,
        question: str,
        input_dataframe: Optional[dict] = None,
        server_mode: Optional[bool] = False,
    ) -> Union[ExitWorkerOutput, AgentOutput]:
        # Make sure you convert the dataframe to a table
        raise NotImplementedError()

    def convert_exit_output_to_agent_output(
        self, exit_output: ExitWorkerOutput
    ) -> AgentOutput:
        return AgentOutput(
            session_name=exit_output.session_name,
            question=exit_output.question,
            db_connection_uri=exit_output.db_connection_uri,
            route_taken=exit_output.route_taken,
            input_dataframe=exit_output.sql_input_dataframe
            or exit_output.analysis_input_dataframe
            or exit_output.plot_input_dataframe,
            output_dataframe=exit_output.sql_output_dataframe
            or exit_output.plot_output_dataframe,
            sql_string=exit_output.sql_string,
            analysis=exit_output.analysis,
            reasoning=exit_output.sql_reasoning
            or exit_output.analysis_reasoning
            or exit_output.plot_reasoning,
            plot_config=exit_output.plot_config,
            image_to_plot=exit_output.image_to_plot,
            followup_route=exit_output.followup_route_to_take,
            followup_suggestion=exit_output.followup_suggestion,
            error_from_pipeline=(
                exit_output.error_from_sql_worker
                or exit_output.error_from_analysis_worker
                or exit_output.error_from_plot_worker
                or exit_output.error_from_followup_worker
            ),
        )

    def __call__(
        self,
        question: str,
        input_dataframe: Optional[dict] = None,
        server_mode: Optional[bool] = False,
        generate_plot_image: Optional[bool] = True,
    ) -> Union[ExitWorkerOutput, AgentOutput]:
        if server_mode:
            kwargs = self.route_worker_kwargs.get("plot", None)
            kwargs = (
                {"plot_image": generate_plot_image}
                if kwargs is None
                else {**kwargs, "plot_image": generate_plot_image}
            )
            self.route_worker_kwargs["plot"] = kwargs

        output = self.run(question=question, input_dataframe=input_dataframe)
        # TODO: Watch out dict here type mismatch with run
        self.history.push(output=output)
        if server_mode:
            output = self.convert_exit_output_to_agent_output(exit_output=output)
        return output
