import os
import sqlite3
from typing import List, Literal, Optional

from premsql.logger import setup_console_logger
from premsql.agents.models import ExitWorkerOutput
from premsql.agents.utils import convert_exit_output_to_agent_output
from premsql.security import quote_sqlite_identifier, validate_session_name

logger = setup_console_logger("[PIPELINE-MEMORY]")



class AgentInteractionMemory:
    def __init__(self, session_name: str, db_path: Optional[str] = None):
        self.session_name = validate_session_name(session_name)
        self.db_path = db_path or os.path.join(
            os.getcwd(), "premsql", "premsql_pipeline_memory.db"
        )

        logger.info(self.db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.create_table_if_not_exists()

    @property
    def table_name(self) -> str:
        return quote_sqlite_identifier(self.session_name)


    def list_sessions(self) -> List[str]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        return [table[0] for table in tables if table[0] != "sqlite_sequence"]

    def create_table_if_not_exists(self):
        cursor = self.conn.cursor()
        cursor.execute(
            f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            db_connection_uri TEXT,
            route_taken TEXT,
            sql_string TEXT,
            sql_reasoning TEXT,
            sql_input_dataframe TEXT,
            sql_output_dataframe TEXT,
            error_from_sql_worker TEXT,
            analysis TEXT,
            analysis_reasoning TEXT,
            analysis_input_dataframe TEXT,
            error_from_analysis_worker TEXT,
            plot_config TEXT,
            plot_input_dataframe TEXT,
            plot_output_dataframe TEXT,
            image_to_plot TEXT,
            plot_reasoning TEXT,
            error_from_plot_worker TEXT,
            followup_route_to_take TEXT,
            followup_suggestion TEXT,
            error_from_followup_worker TEXT,
            additional_input TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        )
        self.conn.commit()

    def get(
        self,
        limit: Optional[int] = None,
        order: Optional[Literal["DESC", "ASC"]] = "DESC",
    ) -> List[tuple[int, ExitWorkerOutput]]:
        cursor = self.conn.cursor()
        query = f"SELECT * FROM {self.table_name} ORDER BY message_id {order}"
        if limit is not None:
            query += " LIMIT ?"
            cursor.execute(query, (limit,))
        else:
            cursor.execute(query)
        rows = cursor.fetchall()
        return [
            {"message_id": row[0], "message": self._row_to_exit_worker_output(row)}
            for row in rows
        ]

    def get_latest_message_id(self) -> Optional[int]:
        cursor = self.conn.cursor()
        query = f"SELECT message_id FROM {self.table_name} ORDER BY message_id DESC LIMIT 1"
        cursor.execute(query)
        row = cursor.fetchone()
        return row[0] if row else None
    
    def generate_messages_from_session(
            self, session_name: str, limit: int = 100, server_mode: bool=False
        ):
        validated_session_name = quote_sqlite_identifier(validate_session_name(session_name))
        cursor = self.conn.cursor()
        query = f"SELECT * FROM {validated_session_name} ORDER BY message_id ASC LIMIT ?"
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()
        for row in rows:
            yield self._row_to_exit_worker_output(row=row) if server_mode == False else convert_exit_output_to_agent_output(
                self._row_to_exit_worker_output(row=row)
            )

    def get_by_message_id(self, message_id: int) -> Optional[dict]:
        cursor = self.conn.cursor()
        query = f"SELECT * FROM {self.table_name} WHERE message_id = ?"
        cursor.execute(query, (message_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_exit_worker_output(row=row)

    def push(self, output: ExitWorkerOutput):
        cursor = self.conn.cursor()
        cursor.execute(
            f"""
        INSERT INTO {self.table_name} (
            question, db_connection_uri, route_taken, sql_string, sql_reasoning,
            sql_input_dataframe, sql_output_dataframe, error_from_sql_worker,
            analysis, analysis_reasoning, analysis_input_dataframe,
            error_from_analysis_worker, plot_config, plot_input_dataframe,
            plot_output_dataframe, image_to_plot, plot_reasoning,
            error_from_plot_worker, followup_route_to_take, followup_suggestion,
            error_from_followup_worker, additional_input
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            self._exit_worker_output_to_tuple(output),
        )
        self.conn.commit()
        logger.info("Pushed to the database")

    def delete_table(self):
        cursor = self.conn.cursor()
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {self.table_name}")
            self.conn.commit()
            logger.info(f"Table '{self.session_name}' has been deleted.")
        except sqlite3.Error as e:
            logger.error(f"Error deleting table '{self.session_name}': {e}")
        finally:
            cursor.close()

    def _row_to_exit_worker_output(self, row) -> ExitWorkerOutput:
        try:
            return ExitWorkerOutput(
                session_name=self.session_name,
                question=row[1],
                db_connection_uri=row[2],
                route_taken=row[3],
                sql_string=row[4],
                sql_reasoning=row[5],
                sql_input_dataframe=self._parse_json(row[6]),
                sql_output_dataframe=self._parse_json(row[7]),
                error_from_sql_worker=row[8],
                analysis=row[9],
                analysis_reasoning=row[10],
                analysis_input_dataframe=self._parse_json(row[11]),
                error_from_analysis_worker=row[12],
                plot_config=self._parse_json(row[13]),
                plot_input_dataframe=self._parse_json(row[14]),
                plot_output_dataframe=self._parse_json(row[15]),
                image_to_plot=row[16],
                plot_reasoning=row[17],
                error_from_plot_worker=row[18],
                followup_route_to_take=row[19],
                followup_suggestion=row[20],
                error_from_followup_worker=row[21],
                additional_input=self._parse_json(row[22]),
            )
        except Exception as e:
            logger.error(f"Error converting row to ExitWorkerOutput: {e}")
            return None

    def _exit_worker_output_to_tuple(self, output: ExitWorkerOutput) -> tuple:
        return (
            output.question,
            output.db_connection_uri,
            output.route_taken,
            output.sql_string,
            output.sql_reasoning,
            self._serialize_json(output.sql_input_dataframe),
            self._serialize_json(output.sql_output_dataframe),
            output.error_from_sql_worker,
            output.analysis,
            output.analysis_reasoning,
            self._serialize_json(output.analysis_input_dataframe),
            output.error_from_analysis_worker,
            self._serialize_json(output.plot_config),
            self._serialize_json(output.plot_input_dataframe),
            self._serialize_json(output.plot_output_dataframe),
            output.image_to_plot,
            output.plot_reasoning,
            output.error_from_plot_worker,
            output.followup_route_to_take,
            output.followup_suggestion,
            output.error_from_followup_worker,
            self._serialize_json(output.additional_input),
        )

    def _parse_json(self, json_str):
        import json

        if not json_str:
            return None
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON: {json_str}")
            return None

    def _serialize_json(self, obj):
        import json

        if obj is None:
            return None
        try:
            return json.dumps(obj)
        except TypeError:
            logger.warning(f"Failed to serialize object to JSON: {obj}")
            return None

    def clear(self):
        cursor = self.conn.cursor()
        cursor.execute(f"DELETE FROM {self.table_name}")
        self.conn.commit()

    def close(self):
        self.conn.close()

    def __del__(self):
        self.close()

    def delete_table(self):
        cursor = self.conn.cursor()
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {self.table_name}")
            self.conn.commit()
            logger.info(f"Table '{self.session_name}' has been deleted.")
        except sqlite3.Error as e:
            logger.error(f"Error deleting table '{self.session_name}': {e}")
        finally:
            cursor.close()

    def get_latest_dataframe(
        self, decision: Literal["plot", "analyse", "query", "followup"]
    ) -> dict:
        contents = self.get(limit=1)
        if not contents:
            return {}

        content = contents[0]["message"]
        if decision == "plot" and content.plot_input_dataframe:
            return content.plot_input_dataframe
        elif decision == "analyse" and content.analysis_input_dataframe:
            return content.analysis_input_dataframe
        elif decision in ("query", "followup") and content.sql_output_dataframe:
            return content.sql_output_dataframe

        return {}
