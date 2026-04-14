from textwrap import dedent
from typing import Literal, Optional

from premsql.executors.base import BaseExecutor
from premsql.generators.base import Text2SQLGeneratorBase
from premsql.logger import setup_console_logger
from premsql.agents.base import Text2SQLWorkerBase
from premsql.agents.baseline.prompts import (
    BASELINE_TEXT2SQL_TABLE_SELECTION_PROMPT,
    BASELINE_TEXT2SQL_WORKER_ERROR_HANDLING_PROMPT,
    BASELINE_TEXT2SQL_WORKER_PROMPT,
    BASELINE_TEXT2SQL_WORKER_PROMPT_NO_FEWSHOT,
)
from premsql.agents.models import Text2SQLWorkerOutput
from premsql.agents.utils import execute_and_render_result
from premsql.security import (
    SecurityValidationError,
    ensure_expected_keys_only,
    parse_structured_output,
)

logger = setup_console_logger("[BASELINE-TEXT2SQL-WORKER]")


class BaseLineText2SQLWorker(Text2SQLWorkerBase):
    def __init__(
        self,
        db_connection_uri: str,
        generator: Text2SQLGeneratorBase,
        helper_model: Optional[Text2SQLGeneratorBase] = None,
        executor: Optional[BaseExecutor] = None,
        include_tables: Optional[list] = None,
        exclude_tables: Optional[list] = None,
        auto_filter_tables: Optional[bool] = False,
        allow_raw_sql: Optional[bool] = False,
    ):
        super().__init__(
            db_connection_uri=db_connection_uri,
            generator=generator,
            executor=executor,
            include_tables=include_tables,
            exclude_tables=exclude_tables,
        )

        self.corrector = helper_model
        self.table_filer_worker = helper_model
        self.auto_filter_tables = auto_filter_tables
        self.allow_raw_sql = allow_raw_sql

    @staticmethod
    def show_dataframe(output: Text2SQLWorkerOutput):
        import pandas as pd

        if output.output_dataframe:
            df = pd.DataFrame(
                output.output_dataframe["data"],
                columns=output.output_dataframe["columns"],
            )
            return df
        return pd.DataFrame({})

    def filer_tables_from_schema(
        self, question: str, additional_input: Optional[str] = None
    ) -> dict:
        prompt = BASELINE_TEXT2SQL_TABLE_SELECTION_PROMPT.format(
            schema=self.db.get_context()["table_info"],
            additional_info=additional_input,
            question=question,
        )
        all_tables = self.db.get_usable_table_names()
        try:
            to_include = []
            output = self.corrector.generate({"prompt": prompt}, postprocess=False)
            output = ensure_expected_keys_only(
                parse_structured_output(output, expected_keys={"include"}),
                expected_keys={"include"},
            )
            if not isinstance(output["include"], list):
                raise SecurityValidationError("Expected 'include' to be a list")
            for table in all_tables:
                if table in output["include"]:
                    to_include.append(table)
        except Exception as e:
            logger.info(f"Error while selecting table: {e}")
            to_include = all_tables
        return to_include

    def _create_prompt(
        self,
        question: str,
        additional_knowledge: Optional[str] = None,
        fewshot_dict: Optional[dict] = None,
        prompt_template: Optional[str] = BASELINE_TEXT2SQL_WORKER_PROMPT,
    ) -> str:
        # Initialize database first
        self.db = self.initialize_database(
            db_connection_uri=self.db_connection_uri, include_tables=None
        )
        
        # Get tables to include
        to_include = []
        if self.auto_filter_tables:
            try:
                to_include = self.filer_tables_from_schema(
                    question=question, additional_input=additional_knowledge
                )
                logger.info(f"Selected tables in schema: {to_include}")
            except Exception as e:
                logger.warning(f"Error filtering tables: {e}. Using all tables.")
        
        # Get schema information
        schema_prompt = self.db.get_context()["table_info"]
        
        # Build knowledge prompt
        knowledge_prompt = ""
        if fewshot_dict:
            template = dedent("""
                Question: {question}
                SQL: {sql}
                """)
            try:
                knowledge_prompt = "".join(
                    template.format(question=sample_question, sql=sample_sql)
                    for sample_question, sample_sql in fewshot_dict.items()
                )
            except Exception as e:
                logger.warning(f"Error formatting fewshot examples: {e}")
        elif to_include and len(to_include) <= 10:
            try:
                self.db._sample_rows_in_table_info = 3
                knowledge_prompt = str(self.db.get_table_info(table_names=to_include))
            except Exception as e:
                logger.warning(f"Error getting table info: {e}")

        try:
            if fewshot_dict or (to_include and len(to_include) <= 10):
                prompt = prompt_template.format(
                    schemas=schema_prompt if fewshot_dict else "",
                    additional_knowledge=additional_knowledge or "",
                    few_shot_examples=knowledge_prompt,
                    question=question,
                )
            else:
                prompt = BASELINE_TEXT2SQL_WORKER_PROMPT_NO_FEWSHOT.format(
                    schemas=schema_prompt,
                    additional_knowledge=additional_knowledge or "",
                    question=question,
                )
            return prompt
        except Exception as e:
            logger.error(f"Error formatting prompt: {e}")
            raise

    def run(
        self,
        question: str,
        additional_knowledge: Optional[str] = None,
        fewshot_dict: Optional[dict] = None,
        temperature: Optional[float] = 0.1,
        max_new_tokens: Optional[int] = 256,
        render_results_using: Optional[Literal["json", "dataframe"]] = "json",
        prompt_template: Optional[str] = BASELINE_TEXT2SQL_WORKER_PROMPT,
        error_handling_prompt_template: Optional[
            str
        ] = BASELINE_TEXT2SQL_WORKER_ERROR_HANDLING_PROMPT,
        **kwargs,
    ) -> Text2SQLWorkerOutput:
        if question.startswith("`") and question.endswith("`"):
            if not self.allow_raw_sql:
                return Text2SQLWorkerOutput(
                    db_connection_uri=self.db_connection_uri,
                    sql_string=None,
                    sql_reasoning=None,
                    input_dataframe=None,
                    output_dataframe={"data": {}, "columns": []},
                    question=question,
                    error_from_model=(
                        "Direct SQL execution is disabled. Use natural language prompts instead."
                    ),
                    additional_input={
                        "additional_knowledge": additional_knowledge,
                        "fewshot_dict": fewshot_dict,
                        "temperature": temperature,
                        "max_new_tokens": max_new_tokens,
                        **kwargs,
                    },
                )
            result = execute_and_render_result(
                db=self.db, sql=question.replace("`", ""), using=render_results_using
            )
            return Text2SQLWorkerOutput(
                db_connection_uri=self.db_connection_uri,
                sql_string=question.replace("`", ""),
                sql_reasoning=None,
                input_dataframe=None,
                output_dataframe=result["dataframe"],
                question=question,
                error_from_model=result["error_from_model"],
                additional_input={
                    "additional_knowledge": additional_knowledge,
                    "fewshot_dict": fewshot_dict,
                    "temperature": temperature,
                    "max_new_tokens": max_new_tokens,
                    **kwargs,
                },
            )


        prompt = self._create_prompt(
            question=question,
            additional_knowledge=additional_knowledge,
            fewshot_dict=fewshot_dict,
            prompt_template=prompt_template,
        )
        generated_sql = self.generator.execution_guided_decoding(
            data_blob={"prompt": prompt, "db_path": self.db_connection_uri},
            executor=self.executor,
            temperature=temperature,
            max_new_tokens=max_new_tokens,
            max_retries=5,
            postprocess=True,
            **kwargs,
        )

        result = execute_and_render_result(
            db=self.db, sql=generated_sql, using=render_results_using
        )

        if result["error_from_model"] is not None:
            logger.info("=> Going for final correction ...")
            generated_sql = self.do_correction(
                question=question,
                result=result,
                additional_knowledge=additional_knowledge,
                fewshot_dict=fewshot_dict,
                prompt_template=prompt_template,
                error_handling_prompt_template=error_handling_prompt_template,
                **kwargs,
            )
            result = execute_and_render_result(
                db=self.db, sql=generated_sql, using=render_results_using
            )

        return Text2SQLWorkerOutput(
            db_connection_uri=self.db_connection_uri,
            sql_string=generated_sql,
            sql_reasoning=None,
            input_dataframe=None,
            output_dataframe=result["dataframe"],  # Truncating to
            question=question,
            error_from_model=result["error_from_model"],
            additional_input={
                "additional_knowledge": additional_knowledge,
                "fewshot_dict": fewshot_dict,
                "temperature": temperature,
                "max_new_tokens": max_new_tokens,
                **kwargs,
            },
        )

    def do_correction(
        self,
        question: str,
        result: dict,
        additional_knowledge: Optional[str] = None,
        fewshot_dict: Optional[dict] = None,
        prompt_template: Optional[str] = BASELINE_TEXT2SQL_WORKER_PROMPT,
        error_handling_prompt_template: Optional[
            str
        ] = BASELINE_TEXT2SQL_WORKER_ERROR_HANDLING_PROMPT,
        **kwargs,
    ):
        if not self.corrector:
            logger.info("Corrector model not defined, no furthur correction possible.")

        error_prompt = error_handling_prompt_template.format(
            existing_prompt=self._create_prompt(
                question=question,
                additional_knowledge=additional_knowledge,
                fewshot_dict=fewshot_dict,
                prompt_template=prompt_template,
            ),
            error_msg=result["error_from_model"],
            sql=result["sql_string"],
        )
        return self.generator.generate(
            data_blob={"prompt": error_prompt}, postprocess=True, **kwargs
        )
