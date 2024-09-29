import sqlite3
import time

from contextlib import contextmanager
from typing import Any, Dict, Generator 
from premsql.executors.base import BaseExecutor
from premsql.logger import setup_console_logger


class OptimizedSQLiteExecutor(BaseExecutor):
    def __init__(self, timeout: float = 1000.0) -> None:
        self.timeout = timeout
        self.logger = setup_console_logger(name="[OPTIMIZED-SQLite-EXEC]")

    @contextmanager
    def get_connection(self, db_path: str) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(db_path, timeout=self.timeout)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.row_factory = sqlite3.Row
        try:
            yield conn 
        finally:
            conn.close() 
        
    def execute_sql(self, sql: str, dsn_or_db_path: str) -> Dict[str, Any]:
        start_time = time.time()
        try:
            with self.get_connection(dsn_or_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("EXPLAIN QUERY PLAN " + sql)
                query_plan = cursor.fetchall()
                
                if any("SCAN TABLE" in str(row) for row in query_plan):
                    self.logger.warn("Warning: Full table scan detected. Consider adding an index.")
                
                cursor.execute(sql)
                result = [dict(row) for row in cursor.fetchall()]
                error = None
        except sqlite3.Error as e:
            result = None
            error = str(e)
        finally:
            end_time = time.time()

        return {
            "result": result,
            "error": error,
            "execution_time": end_time - start_time,
        }
    
    def match_sqls(self, predicted_sql: str, gold_sql: str, dsn_or_db_path: str) -> Dict[str, Any]:
        with self.get_connection(dsn_or_db_path) as conn:
            prediction = self.execute_sql(predicted_sql, dsn_or_db_path)
            gold = self.execute_sql(gold_sql, dsn_or_db_path)

        if prediction["error"]:
            return {"result": 0, "error": prediction["error"]}

        is_match = set(map(tuple, prediction["result"])) == set(map(tuple, gold["result"]))
        return {
            "result": int(is_match),
            "error": None if is_match else "Table mismatch",
        }

    def iterated_execution(self, predicted_sql: str, gold_sql: str, dsn_or_db_path: str, num_iterations: int) -> Dict[str, Any]:
        is_match = self.match_sqls(predicted_sql, gold_sql, dsn_or_db_path)

        if is_match["result"] == 1:
            with self.get_connection(dsn_or_db_path) as conn:
                diff_list = []
                for _ in range(num_iterations):
                    gold_time = self.execute_sql(gold_sql, dsn_or_db_path)["execution_time"]
                    predicted_time = self.execute_sql(predicted_sql, dsn_or_db_path)["execution_time"]
                    diff_list.append(predicted_time / gold_time if gold_time > 0 else float('inf'))

            processed_diff_list = self.clean_abnormal(diff_list)
            return {
                "result": sum(processed_diff_list) / len(processed_diff_list) if processed_diff_list else 0,
                "error": None,
            }
        return {"result": 0, "error": is_match["error"]}



class SQLiteExecutor(BaseExecutor):
    def execute_sql(self, sql: str, dsn_or_db_path: str) -> dict:
        conn = sqlite3.connect(dsn_or_db_path)
        cursor = conn.cursor()

        start_time = time.time()
        try:
            cursor.execute(sql)
            result = cursor.fetchall()
            error = None
        except Exception as e:
            result = None
            error = str(e)

        end_time = time.time()
        cursor.close()
        conn.close()

        result = {
            "result": result,
            "error": error,
            "execution_time": end_time - start_time,
        }
        return result
