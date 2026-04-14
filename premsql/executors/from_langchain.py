import time
from typing import Union

from langchain_community.utilities.sql_database import SQLDatabase

from premsql.executors.base import BaseExecutor
from premsql.security import enforce_read_only_sql
from premsql.utils import convert_sqlite_path_to_dsn


class ExecutorUsingLangChain(BaseExecutor):

    def execute_sql(self, sql: str, dsn_or_db_path: Union[str, SQLDatabase]) -> dict:
        if isinstance(dsn_or_db_path, str):
            if dsn_or_db_path.endswith("sqlite"):
                dsn_or_db_path = convert_sqlite_path_to_dsn(path=dsn_or_db_path)
            db = SQLDatabase.from_uri(dsn_or_db_path)
        else:
            db = dsn_or_db_path

        safe_sql = enforce_read_only_sql(sql)
        start_time = time.time()
        response = db.run_no_throw(safe_sql)
        end_time = time.time()

        error = response if response.startswith("Error") else None
        return {
            "result": None if error else response,
            "error": error,
            "execution_time": end_time - start_time,
        }
