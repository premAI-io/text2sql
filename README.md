# PremSQL
End-to-End Local-First Text-to-SQL Pipelines

PremSQL is an open-source library designed to help developers create secure, fully local Text-to-SQL solutions using small language models. It provides all the essential tools to build and deploy end-to-end Text-to-SQL pipelines with customizable components, making it ideal for secure, autonomous AI-powered data analysis.

![alt architecture](/assets/architecture.png)

## News and blogs

- [Sep 20th 2024] First release of [Prem-1B-SQL](https://huggingface.co/premai-io/prem-1B-SQL) (51.54% on BirdBench private dataset) | [Blog post](https://blog.premai.io/prem-1b-sql-fully-local-performant-slm-for-text-to-sql/)
- [Sep 10th 2024] First release of PremSQL | [Blog Post](https://blog.premai.io/premsql-towards-end-to-end-local-text-to-sql-pipelines-2/)
- [Blog post]: [Using PremSQL to evaluate different open and closed source models](https://blog.premai.io/premsql-towards-end-to-end-local-text-to-sql-pipelines-2/)
- [Blog post]: [State of Text to SQL 2024](https://blog.premai.io/state-of-text2sql-2024/)

## 🚀 Features

- **Local-First**: Avoid third-party closed-source providers and keep your data secure.
- **Customizable Datasets**: Create, fine-tune, and evaluate models with built-in or custom datasets.
- **Robust Executors and Evaluators**: Easily connect to databases and assess model performance.
- **Advanced Generators**: Convert natural language prompts into executable SQL queries.
- **Error Handling and Self-Correction**: Automatically correct SQL queries during inference.
- **Fine-Tuning Support**: Fine-tune models with LoRA, QLoRA, or full fine-tuning strategies.
- **End-to-End Pipelines**: Seamlessly integrate all components for autonomous data analysis.

Last but not the least, all the features are extendible for your very own customization and private data. 

## 📚 Table of Contents

- [PremSQL](#premsql)
  - [🚀 Features](#-features)
  - [📚 Table of Contents](#-table-of-contents)
  - [🛠️ Installation](#️-installation)
  - [🚀 Quickstart](#-quickstart)
  - [📦 Components Overview](#-components-overview)
    - [Datasets](#datasets)
    - [Executors](#executors)
    - [Evaluators](#evaluators)
    - [Generators](#generators)
    - [Error Handling](#error-handling)
    - [Tuner](#tuner)
    - [Pipelines](#pipelines)
  - [🤝 Contributing](#-contributing)
  - [🛣️ Roadmap](#️-roadmap)
  - [📝 License](#-license)

## 🛠️ Installation

PremSQL requires Python 3.8 or higher. Install the library via pip:

```bash
pip install premsql
```

## 🚀 Quickstart

Here’s a quick example of how to use PremSQL to generate SQL queries from natural language inputs:

```python
from premsql.pipelines import SimpleText2SQLAgent
from premsql.generators import Text2SQLGeneratorHF
from premsql.executors import SQLiteExecutor

# Provide a SQLite file here.
# You may also pass in a SQLDatabase object directly:

# from langchain_community.utilities.sql_database import SQLDatabase
# dsn_or_db_path = SQLDatabase.from_uri("sqlite:///data/db/california_schools.sqlite")

# See documentation for more customization

dsn_or_db_path = "sqlite:///data/db/california_schools.sqlite"

agent = SimpleText2SQLAgent(
    dsn_or_db_path=dsn_or_db_path,
    generator=Text2SQLGeneratorHF(
        model_or_name_or_path="premai-io/prem-1B-SQL",
        experiment_name="simple_pipeline",
        device="cuda:0",
        type="test"
    ),
)

question = "please list the phone numbers of the direct charter-funded schools that are opened after 2000/1/1"

response = agent.query(question)
response["table"]

```

## 📦 Components Overview

### [Datasets](https://docs.premai.io/premsql/introduction)

PremSQL provides a simple API to use various pre-processed datasets for Text-to-SQL tasks. Text-to-SQL is complex as it requires data dependencies on databases and tables. The premsql datasets help streamline this by providing easy access to datasets and enabling you to create your own datasets with private databases.

Currently, the following datasets are readily available:

1. [BirdBench Dataset](https://huggingface.co/datasets/premai-io/birdbench)
2. [Spider Unified Datasets](https://huggingface.co/datasets/premai-io/spider)
3. [Domains Dataset](https://huggingface.co/datasets/premai-io/domains)
4. [Gretel AI Dataset](https://huggingface.co/datasets/gretelai/synthetic_text_to_sql)


**Example usage:**

```python
from premsql.datasets import Text2SQLDataset

bird_dataset = Text2SQLDataset(
    dataset_name='bird', split="train", force_download=False,
    dataset_folder="/path/to/your/data" # change this to the path where you want to store the dataset
)

```
### Generators

PremSQL generators are responsible for converting natural language questions into SQL queries. Think of these as modular inference APIs specific to text-to-SQL. You can integrate various third-party APIs, models, or custom pipelines.

**Example:**

```python
from premsql.generators import Text2SQLGeneratorHF
from premsql.datasets import Text2SQLDataset

# Define a dataset
dataset = bird_dataset = Text2SQLDataset(
    dataset_name='bird', split="train", force_download=False,
    dataset_folder="/path/to/dataset"
).setup_dataset(num_rows=10, num_fewshot=3)

# Define a generator 
generator = Text2SQLGeneratorHF(
    model_or_name_or_path="premai-io/prem-1B-SQL",
    experiment_name="test_generators",
    device="cuda:0",
    type="test"
)

# Generate on the full dataset
responses = generator.generate_and_save_results(
    dataset=bird_dataset,
    temperature=0.1,
    max_new_tokens=256
)

print(responses)
```
Results are saved in the experiment_path as predict.json. 

We also support execution guided decoding. This strategy executes the generated SQL against the DB and, if it fails, uses the error message for correction, repeating until it gets a valid result or the retries run out.

![alt text](/assets/execution_guided_decoding.png)

A quick glance on execution guided decoding:

```python
from premsql.executors import SQLiteExecutor

executor = SQLiteExecutor()
response = generator.generate_and_save_results(
    dataset=bird_dataset,
    temperature=0.1,
    max_new_tokens=256,
    force=True,
    executor=executor,
    max_retries=5 # this is optional (default is already set to 5)
)
```

### [Executors](https://docs.premai.io/premsql/executors)

An executor executes the generated SQL queries against the database and fetches the results. It is a crucial component in the Text-to-SQL pipeline, as it ensures that the generated SQL queries are valid and return the expected results. PremSQL supports a native executor for SQLite databases and also supports [LangChain's SQLDatabase](https://python.langchain.com/v0.2/docs/integrations/tools/sql_database/)
as an executor. 

**Example usage**

```python
from premsql.executors import SQLiteExecutor

# Instantiate the executor
executor = SQLiteExecutor()

# Set a sample dataset path 
db_path = "./data/db/california_schools.sqlite"
sql = 'SELECT movie_title FROM movies WHERE movie_release_year = 1945 ORDER BY movie_popularity DESC LIMIT 1'

# execute the SQL
result = executor.execute_sql(
    sql=sql,
    dsn_or_db_path=db_path
)

print(result)
```

This will show:

```python
{'result': [('Brief Encounter',)], 'error': None, 'execution_time': 0.03717160224914551}
```


### [Evaluators](https://docs.premai.io/premsql/evaluators)

Executors connect to databases and execute SQL, while evaluators assess the performance of your models against predefined metrics like Execution Accuracy (EX) and Valid Efficiency Score (VES).

**Example Usage:**

```python
from premsql.executors import SQLiteExecutor
from premsql.evaluator import Text2SQLEvaluator

# Define the executor 
executor = SQLiteExecutor()

# Define the evaluator 
evaluator = Text2SQLEvaluator(
    executor=executor,
    experiment_path=generator.experiment_path
)

# Now evaluate the models 
results = evaluator.execute(
    metric_name="accuracy",
    model_responses=response,
    filter_by="db_id",
    meta_time_out=10
)

print(results)
```

Using the `filter_by` option to filter results by `db_id` allows you to see overall accuracy and its distribution across different databases. If a key like `difficulty` is available, it will show performance distribution over various difficulty levels. Filtering evaluations by available keys helps in analyzing and understanding model performance empirically. Below is a visualization of model performance across different databases based on the applied filters.

![alt text](/assets/eval_result_filtered.png)


### [Error Handling](https://docs.premai.io/premsql/error_dataset)

Error-handling prompts are crucial for refining model performance, especially in complex tasks like Text-to-SQL generation. The prompts help the model learn how to handle errors by providing additional context and guidance based on past mistakes. By training on these prompts, the model can self-correct during inference, improving the quality of its output.

**Example Error Correction Prompt:**

```plaintext
{existing_prompt}

# Generated SQL: {sql}

## Error Message

{error_msg}

Carefully review the original question and error message, then rewrite the SQL query to address the identified issues.
```

To create a self-correction / error-correction dataset:

- You start with an existing training dataset
- You run an evaluation on that training dataset using an un-trained model.
- You gather the data and pass it to the error-handling prompt 
- Finally, you save the results ready to be used for fine-tuning. 

Here is the code to get started to make a self-correction dataset using existing datasets:

```python
from premsql.datasets.error_dataset import ErrorDatasetGenerator
from premsql.generators.huggingface import Text2SQLGeneratorHF
from premsql.executors.from_langchain import ExecutorUsingLangChain
from premsql.datasets import BirdDataset

generator = Text2SQLGeneratorHF(
    model_or_name_or_path="premai-io/prem-1B-SQL",
    experiment_name="testing_error_gen",
    type="train", # do not type: 'test' since this will be used during training
    device="cuda:0"
)

executor = ExecutorUsingLangChain()

bird_train = BirdDataset(
    split="train",
    dataset_folder="/path/to/dataset"
).setup_dataset(num_rows=10)

error_dataset_gen = ErrorDatasetGenerator(generator=generator, executor=executor)

error_dataset = error_dataset_gen.generate_and_save(
    datasets=bird_train,
    force=True
)

```


### [Tuner](https://docs.premai.io/premsql/tuner)

`premsql tuner` is a module designed to fine-tune models specifically for text-to-SQL tasks. The module offers multiple ways of fine-tuning, providing flexibility based on your project's needs. 

### Supported Fine-Tuning Methods

1. **Full Fine-Tuning**: Standard model fine-tuning with all its parameters.
2. **PEFT using LoRA**: Parameter-efficient-fine-tuning with LoRA (Low-Rank Adaptation) for faster and more efficient training.
3. **PEFT using QLoRA**: Another PEFT approach using Quantized LoRA, optimizing resource use during training.

In addition to these methods, you can create custom fine-tuning pipelines using the components and tools provided by premsql.

### [Pipelines](https://docs.premai.io/premsql/pipelines)

PremSQL pipelines are end-to-end solutions that connect to your database and generate SQL queries from natural language questions, providing complete control over your data analysis workflows.

**Example Simple Pipeline:**

```python
from premsql.pipelines.simple import SimpleText2SQLAgent
from premsql.generators.huggingface import Text2SQLGeneratorHF
from langchain_community.utilities.sql_database import SQLDatabase
from premsql.utils import convert_sqlite_path_to_dsn

# Change it some SQLite database path or any other DB URI connection.
dsn_or_db_path = convert_sqlite_path_to_dsn(
  "../data/bird/test/test_databases/california_schools/california_schools.sqlite"   
)
db = SQLDatabase.from_uri(dsn_or_db_path)

agent = SimpleText2SQLAgent(
    dsn_or_db_path=db,
    generator=Text2SQLGeneratorHF(
        model_or_name_or_path="premai-io/prem-1B-SQL",
        experiment_name="test_nli",
        device="cuda:0",
        type="test"
    ),
)

response = agent.query(
    question="please list the phone numbers of the direct charter-funded schools that are opened after 2000/1/1",
)

response["table"]

```

## 🤝 Contributing

We welcome contributions from the community! If you’d like to contribute to PremSQL, please follow these guidelines:

1. **Fork the repository** and clone your fork.
2. **Create a new branch** for your feature or bug fix.
3. **Make your changes** and ensure the code passes all tests.
4. **Submit a pull request** with a clear description of your changes.

For detailed guidelines, please check the [CONTRIBUTING.md](CONTRIBUTING.md).

## 🛣️ Roadmap

PremSQL is continuously evolving, with exciting features planned for future releases:

- **Synthesizer Component**: A tool to generate synthetic datasets from private data, enabling fully private text-to-SQL workflows and enhancing model fine-tuning capabilities.
- **Agentic Pipelines with Function-Calling Features**: Advanced pipelines with graph plotting, natural language analysis, and other enhancements to provide a more versatile and powerful system.
- **Training Better Small Language Models**: Ongoing training and optimization of small language models specifically tailored to PremSQL’s unique requirements, ensuring efficient and effective performance in text-to-SQL tasks.
- **Optimization of Generators and Executors**: Improvements to enhance the robustness of existing components, including parallel processing to speed up generation and execution times.
- **Standard Tests and Stability Improvements**: Introduction of comprehensive tests for greater stability of the library and the planned rollout of a simple user interface to improve the overall user experience.

Stay tuned for these exciting updates! We encourage you to contribute and provide feedback to help us shape the future of PremSQL.


## 📝 License

PremSQL is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.
