from typing import Any, Dict, Literal

import pandas as pd

from premsql.executors.from_langchain import SQLDatabase
from premsql.logger import setup_console_logger
from premsql.agents.models import AgentOutput, ExitWorkerOutput
from premsql.security import UnsafeSQLQuery, enforce_read_only_sql

logger = setup_console_logger("[PIPELINE-UTILS]")


def convert_df_to_dict(df: pd.DataFrame):
    return {"data": df.to_dict(), "columns": list(df.keys())}


def execute_and_render_result(
    db: SQLDatabase, sql: str, using: Literal["dataframe", "json"]
):
    try:
        safe_sql = enforce_read_only_sql(sql)
    except UnsafeSQLQuery as exc:
        return _render_error(str(exc), sql, using)

    result = db.run_no_throw(command=safe_sql, fetch="cursor")

    if isinstance(result, str):
        return _render_error(result, safe_sql, using)
    return _render_data(result, safe_sql, using)


def _render_error(error: str, sql: str, using: str) -> Dict[str, Any]:
    to_show = {"sql_string": sql, "error_from_model": error, "dataframe": None}

    if using == "dataframe":
        to_show["dataframe"] = pd.DataFrame()  # empty DataFrame
    elif using == "json":
        to_show["dataframe"] = {"data": {}, "columns": []}  # empty JSON structure
    return to_show


def _render_data(result, sql: str, using: str) -> Dict[str, Any]:
    table = pd.DataFrame(data=result.fetchall(), columns=result.keys())
    if len(table) > 200:
        logger.info("Truncating output table to first 200 rows only")
        table = table.iloc[:200, :]
    
    if any(table.columns.duplicated()):
        logger.info(f"Found duplicate columns: {table.columns[table.columns.duplicated()].tolist()}")
        # Create unique column names by adding suffixes
        table.columns = [f"{col}_{i}" if i > 0 else col 
                        for i, col in enumerate(table.columns)]
        logger.info(f"Renamed columns to: {table.columns.tolist()}")

    to_show = {"sql_string": sql, "error_from_model": None, "dataframe": table}

    if using == "json":
        to_show["dataframe"] = {"columns": list(table.columns), "data": table.to_dict()}
    return to_show



def convert_exit_output_to_agent_output(exit_output: ExitWorkerOutput) -> AgentOutput:
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
