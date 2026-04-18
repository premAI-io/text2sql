from abc import ABC, abstractmethod

import numpy as np


class BaseExecutor(ABC):
    @abstractmethod
    def execute_sql(self, sql: str, dsn_or_db_path: str) -> dict:
        return {"result": None, "execution_time": None, "error": None}

    def match_sqls(
        self, predicted_sql: str, gold_sql: str, dsn_or_db_path: str
    ) -> bool:
        prediction = self.execute_sql(sql=predicted_sql, dsn_or_db_path=dsn_or_db_path)
        gold = self.execute_sql(sql=gold_sql, dsn_or_db_path=dsn_or_db_path)
        if prediction["error"]:
            return {
                "result": 0,
                "error": prediction["error"],
            }

        is_match = set(prediction["result"]) == set(gold["result"])
        return {
            "result": int(is_match),
            "error": None if is_match else "Table mismatch",
        }

    def clean_abnormal(self, input: list[float]) -> list[float]:
        input_array = np.asarray(input)
        mean = np.mean(input_array)
        std = np.std(input_array)
        return [x for x in input_array if mean - 3 * std < x < mean + 3 * std]

    def iterated_execution(
        self,
        predicted_sql: str,
        gold_sql: str,
        dsn_or_db_path: str,
        num_iterations: int,
    ) -> dict:
        is_match = self.match_sqls(
            predicted_sql=predicted_sql,
            gold_sql=gold_sql,
            dsn_or_db_path=dsn_or_db_path,
        )

        if is_match["result"] == 1:
            diff_list = [
                # Bug fix: denominator must use predicted_sql, not gold_sql.
                # The original code divided gold_time / gold_time (always 1.0),
                # making VES meaningless. Correct formula: gold_time / predicted_time.
                self.execute_sql(sql=gold_sql, dsn_or_db_path=dsn_or_db_path)[
                    "execution_time"
                ]
                / self.execute_sql(sql=predicted_sql, dsn_or_db_path=dsn_or_db_path)[
                    "execution_time"
                ]
                for _ in range(num_iterations)
            ]
            processed_diff_list = self.clean_abnormal(diff_list)
            return {
                "result": sum(processed_diff_list) / len(processed_diff_list),
                "error": None,
            }
        return {"result": 0, "error": is_match["error"]}
