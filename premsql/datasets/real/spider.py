from pathlib import Path
from typing import Optional, Union

from huggingface_hub import snapshot_download

from premsql.datasets.base import Text2SQLBaseDataset
from premsql.logger import setup_console_logger

logger = setup_console_logger("[SPIDER-DATASET]")


class SpiderUnifiedDataset(Text2SQLBaseDataset):
    def __init__(
        self,
        split: str,
        dataset_folder: Optional[Union[str, Path]] = "./data",
        hf_token: Optional[str] = None,
        force_download: Optional[bool] = False,
    ):
        dataset_folder = Path(dataset_folder)
        spider_folder = dataset_folder / "spider"
        if not spider_folder.exists() or force_download:
            spider_folder.mkdir(parents=True, exist_ok=True)

            # Download it from hf hub
            snapshot_download(
                repo_id="premai-io/spider",
                repo_type="dataset",
                local_dir=dataset_folder / "spider",
                force_download=force_download,
            )

        assert split in ["train", "validation"], ValueError(
            "Split should be either train or validation"
        )
        json_file_name = "train.json" if split == "train" else "validation.json"
        super().__init__(
            split=split,
            dataset_path=spider_folder,
            database_folder_name="database",
            json_file_name=json_file_name,
            hf_token=hf_token,
        )
        logger.info("Loaded Spider Dataset")

        # An extra step for Spider Dataset so that it can be
        # compatible with the Base dataset and Base instance

        for content in self.dataset:
            content["SQL"] = content["query"]

    def setup_dataset(
        self,
        filter_by: tuple | None = None,
        num_rows: int | None = None,
        num_fewshot: int | None = None,
        model_name_or_path: str | None = None,
        prompt_template: str | None = None,
        tokenize: bool | None = False 
    ):
        logger.info("Setting up Spider Dataset")
        return super().setup_dataset(
            filter_by=filter_by,
            num_rows=num_rows,
            model_name_or_path=model_name_or_path,
            tokenize=tokenize,
            prompt_template=prompt_template,
            num_fewshot=num_fewshot
        )
