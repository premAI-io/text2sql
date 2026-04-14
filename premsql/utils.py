import json
import os
import random
import re
import sqlite3
from collections import defaultdict
from pathlib import Path
from textwrap import dedent
from typing import Optional, Sequence, Union

from tqdm.auto import tqdm
from premsql.logger import setup_console_logger

logger = setup_console_logger(name="[UTILS]")

try:
    from transformers import PreTrainedTokenizer
except ImportError:
    logger.warn("Unable to use transformers. Install using: pip install transformers")


def convert_sqlite_path_to_dsn(path: str):
    sqlite3_pattern = r"^sqlite:\/\/\/.*"
    if re.match(sqlite3_pattern, path):
        return path
    return f"sqlite:///{os.path.abspath(path)}"


def convert_sqlite_dsn_to_path(dsn: str) -> str:
    sqlite3_pattern = r"^sqlite:\/\/\/(.*)"
    match = re.match(sqlite3_pattern, dsn)
    if match:
        return os.path.abspath(match.group(1))
    return dsn


def print_data(data: dict):
    if "prompt" in data:
        prompt = data["prompt"]
        data["prompt"] = prompt[:100] + "...." + prompt[-100:]

    elif "prompt" in data["raw"]:
        prompt = data["raw"]["prompt"]
        data["raw"]["prompt"] = prompt[:100] + "...." + prompt[-100:]

    else:
        raise ValueError("Prompt key not found in data")

    return data


def save_to_json(save_path: Union[str, Path], json_object: dict):
    try:
        save_path = Path(save_path) if isinstance(save_path, str) else save_path
        with open(save_path, "w") as json_file:
            json.dump(json_object, json_file, indent=4, ensure_ascii=False)
        logger.info(f"Saved JSON in: {save_path}")
    except Exception as e:
        logger.error(f"Unable to save JSON, Error: {e}")


def load_from_json(result_json_path: str) -> dict:
    try:
        with open(result_json_path, "r") as json_file:
            return json.load(json_file)
    except Exception as e:
        logger.error(f"Unable to load JSON, Error: {e}")


def sqlite_schema_prompt(db_path: str) -> str:
    schemas = {}
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    for table in tables:
        table_name = table[0]
        if table_name == "sqlite_sequence":
            continue
        # Use parameterized query instead of f-string for safety
        cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?;",
            (table_name,)
        )
        create_table_sql = cursor.fetchone()
        if create_table_sql:
            schemas[table_name] = create_table_sql[0]
        else:
            schemas[table_name] = "Schema does not exist"

    schema_prompt = "\n".join(
        schemas[table[0]] for table in tables if table[0] != "sqlite_sequence"
    )
    return schema_prompt


def get_random_few_shot_prompts(dataset: list[dict], num_few_shot: int):
    assert "db_id" in dataset[0], ValueError(
        "db_id key should be present to use this function"
    )

    grouped_content = defaultdict(list)
    few_shot_prompts = {}
    template = dedent(
        """
    Question: {question}
    SQL: {sql}
    """
    )

    for content in dataset:
        grouped_content[content["db_id"]].append(content)

    for db_id, contents in grouped_content.items():
        num_few_shot = min(num_few_shot, len(contents))
        random_sample = random.sample(contents, num_few_shot)

        few_shot_prompt = "".join(
            template.format(question=element["question"], sql=element["SQL"])
            for element in random_sample
        )
        few_shot_prompts[db_id] = few_shot_prompt
    return few_shot_prompts


def get_accepted_filters(data: list[dict]) -> Sequence[str]:
    key_num_mapping = {}
    for key in data[0].keys():
        key_num_mapping[key] = len(set([content[key] for content in data]))

    accepted_keys = []
    for key, num in key_num_mapping.items():
        if num < len(data) * 0.5 and key != "db_path":
            accepted_keys.append(key)
    return accepted_keys


def filter_options(
    data: list[dict], filter_by: tuple, accepted_keys: Optional[Sequence[str]] = None
):
    filter_key, filter_value = filter_by
    accepted_keys = (
        get_accepted_filters(data=data) if accepted_keys is None else accepted_keys
    )

    assert filter_key in accepted_keys, ValueError(
        f"Filtering is supported for keys: `{''.join(accepted_keys)}`"
    )
    for key in accepted_keys:
        if filter_key == key:
            accepted_values = set([content[key] for content in data])
            assert filter_value in accepted_values, ValueError(
                f"Available values for key: {key} are: {', '.join(accepted_values)}"
            )

    filtered_data = [content for content in data if content[filter_key] == filter_value]
    return filtered_data


def tokenize_fn(strings: Sequence[str], tokenizer: "PreTrainedTokenizer") -> dict:
    """Tokenizes a list of string"""
    tokenized_list = [
        tokenizer(
            text=text,
            return_tensors="pt",
            padding="longest",
            max_length=tokenizer.model_max_length,
            truncation=False,
        )
        for text in tqdm(strings, total=len(strings), desc="Tokenizing")
    ]
    input_ids = labels = [tokenized.input_ids[0] for tokenized in tokenized_list]
    input_ids_lens = label_ids_lens = [
        tokenized.input_ids.ne(tokenizer.pad_token_id).sum().item()
        for tokenized in tokenized_list
    ]
    return dict(
        input_ids=input_ids,
        labels=labels,
        input_ids_lens=input_ids_lens,
        label_ids_lens=label_ids_lens,
    )
