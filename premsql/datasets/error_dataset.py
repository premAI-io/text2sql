import json
from pathlib import Path
from typing import Optional, Sequence

from tqdm.auto import tqdm

from premsql.datasets.base import (
    SupervisedDatasetForTraining,
    Text2SQLBaseDataset,
    Text2SQLBaseInstance,
)
from premsql.evaluator.base import BaseExecutor, Text2SQLEvaluator
from premsql.generators.base import Text2SQLGeneratorBase
from premsql.logger import setup_console_logger
from premsql.prompts import ERROR_HANDLING_PROMPT

logger = setup_console_logger("[ERROR-HANDLING-DATASET]")


class ErrorDatasetInstance(Text2SQLBaseInstance):

    def __init__(self, dataset: list[dict]) -> None:
        super().__init__(dataset=dataset)

    def apply_prompt(self, prompt_template: Optional[str] = ERROR_HANDLING_PROMPT):
        data_to_return = []
        for content in tqdm(
            self.dataset, total=len(self.dataset), desc="Applying error prompt"
        ):
            assert "error" in content, "key error is not present"
            error_msg = content["error"]

            if error_msg is not None:
                prompt = content["prompt"].split("# SQL:")[0].strip()
                prediction = content["generated"]
                error_prompt = prompt_template.format(
                    existing_prompt=prompt, sql=prediction, error_msg=error_msg
                )
                data_to_return.append(
                    {
                        "db_id": content["db_id"],
                        "question": content["question"],
                        "SQL": content["SQL"],
                        "prompt": error_prompt,
                        "db_path": content["db_path"],
                    }
                )
        return data_to_return


class ErrorDatasetGenerator:
    @classmethod
    def from_existing(
        cls,
        experiment_name: str,
        experiment_folder: Optional[str] = None,
        tokenize_model_name_or_path: Optional[str] = None,
        hf_token: Optional[str] = None,
    ) -> dict:
        experiment_folder = Path("./experiments") or Path(experiment_folder)
        experiment_path = (
            experiment_folder / "train" / experiment_name / "error_dataset.json"
        )
        if not experiment_path.exists():
            raise FileNotFoundError(f"Path {experiment_path} does not exists")
        dataset = json.load(open(experiment_path, "r"))
        return (
            ErrorDatasetInstance(dataset=dataset)
            if not tokenize_model_name_or_path
            else SupervisedDatasetForTraining(
                dataset=dataset,
                model_name_or_path=tokenize_model_name_or_path,
                hf_token=hf_token,
            )
        )

    def __init__(
        self,
        generator: Text2SQLGeneratorBase,
        executor: BaseExecutor,
    ):
        self.generator = generator
        self.evaluator = Text2SQLEvaluator(
            executor=executor, experiment_path=self.generator.experiment_path
        )

    def generate_and_save(
        self,
        datasets: Sequence[Text2SQLBaseDataset],
        path_to_save: Optional[str] = None,
        force: Optional[bool] = False,
        tokenize: Optional[bool] = False,
        prompt_template: Optional[str] = ERROR_HANDLING_PROMPT,
        hf_token: Optional[str] = None,
    ) -> None:

        path_to_save = (
            (self.generator.experiment_path / "error_dataset.json")
            if path_to_save is None
            else Path(path_to_save)
        )
        if path_to_save.exists() and force == False:
            logger.info("Error dataset already exists")
            with open(path_to_save, "r") as json_file:
                data_to_return = json.load(json_file)
            return data_to_return

        responses = self.generator.generate_and_save_results(
            dataset=datasets, temperature=0.1, max_new_tokens=256, force=force
        )
        logger.info("Starting Evaluation")
        _ = self.evaluator.execute(
            metric_name="accuracy",
            model_responses=responses,
        )
        del responses

        # Now iterate over the error dataset
        with open(self.generator.experiment_path / "predict.json", "r") as file:
            error_dataset = json.load(file)

        error_instances = ErrorDatasetInstance(dataset=error_dataset).apply_prompt(
            prompt_template=prompt_template
        )

        with open(path_to_save, "w") as json_file:
            json.dump(error_instances, json_file, indent=4)

        return (
            error_instances
            if not tokenize
            else SupervisedDatasetForTraining(
                dataset=error_instances,
                model_name_or_path=self.generator.model_name_or_path,
                hf_token=hf_token,
            )
        )
