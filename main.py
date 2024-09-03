from text2sql.datasets.real.bird import BirdDataset
from text2sql.datasets.real.domains import DomainsDataset
from text2sql.datasets.real.spider import SpiderDataset
from text2sql.datasets.synthetic.gretel import GretelAIDataset

# dataset = BirdDataset(split="train", force_download=False).setup_dataset(
#     model_name_or_path="premai-io/prem-1B-SQL", num_fewshot=3, num_rows=3
# )
# print(dataset[0])


dataset = SpiderDataset(split="train", force_download=False).setup_dataset(
    model_name_or_path="premai-io/prem-1B-SQL", num_fewshot=3, num_rows=3
)


# dataset = DomainsDataset(split="train", force_download=False).setup_dataset(
#     model_name_or_path="premai-io/prem-1B-SQL", num_fewshot=3, num_rows=3
# )
# print(dataset[0])

dataset = GretelAIDataset(force_download=True).setup_dataset(
    model_name_or_path="premai-io/prem-1B-SQL", num_fewshot=3, num_rows=3
)
