from pathlib import Path
from typing import Optional, Union

from premsql.datasets.base import StandardDataset, Text2SQLBaseDataset
from premsql.datasets.real.bird import BirdDataset
from premsql.datasets.real.domains import DomainsDataset
from premsql.datasets.real.spider import SpiderUnifiedDataset
from premsql.datasets.synthetic.gretel import GretelAIDataset
from premsql.utils import get_accepted_filters


class Text2SQLDataset:
    def __init__(
        self,
        dataset_name: str,
        split: str,
        dataset_folder: Optional[Union[str, Path]] = "./data",
        hf_token: Optional[str] = None,
        force_download: Optional[bool] = False,
        **kwargs
    ):
        assert dataset_name in ["bird", "domains", "spider", "gretel"], ValueError(
            "Dataset should be one of bird, domains, spider, gretel"
        )
        dataset_mapping = {
            "bird": BirdDataset,
            "domains": DomainsDataset,
            "spider": SpiderUnifiedDataset,
            "gretel": GretelAIDataset,
        }
        self._text2sql_dataset: Text2SQLBaseDataset = dataset_mapping[dataset_name](
            split=split,
            dataset_folder=dataset_folder,
            hf_token=hf_token,
            force_download=force_download,
            **kwargs
        )

    @property
    def raw_dataset(self):
        return self._text2sql_dataset.dataset

    @property
    def filter_availables(self):
        return get_accepted_filters(data=self._text2sql_dataset.dataset)

    def setup_dataset(
        self,
        filter_by: tuple | None = None,
        num_rows: int | None = None,
        num_fewshot: int | None = None,
        model_name_or_path: str | None = None,
        prompt_template: str | None = None,
        tokenize: bool | None = False 
    ):
        return self._text2sql_dataset.setup_dataset(
            filter_by=filter_by,
            num_rows=num_rows,
            model_name_or_path=model_name_or_path,
            tokenize=tokenize,
            prompt_template=prompt_template,
            num_fewshot=num_fewshot
        )


__all__ = [
    "StandardDataset",
    "GretelAIDataset",
    "SpiderUnifiedDataset",
    "BirdDataset",
    "DomainsDataset",
    "Text2SQLDataset",
]
