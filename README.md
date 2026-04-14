# PremSQL | Easy to use fully local RAG on Databases

[![PyPI Downloads](https://static.pepy.tech/badge/premsql)](https://pepy.tech/projects/premsql)
<a href="https://huggingface.co/premai-io/prem-1B-SQL"><img src="https://img.shields.io/badge/HuggingFace (downloads till Feb14: 26K+) -yellow"></a>

PremSQL is an open-source library designed to help developers create secure, fully local Text-to-SQL solutions using small language models. It provides all the essential tools to build and deploy end-to-end Text-to-SQL pipelines with customizable components, making it ideal for secure, autonomous AI-powered data analysis.

![alt architecture](/assets/architecture.png)

## New: PremSQL Playground, Agents and API

We just rleased the latest version of PremSQL. It comes with the following:

- **PremSQL Agents:** Using PremSQL agents you can make analysis, plot charts and query to databases all using Natural Language. For now it comes with a baseline level agent. Using our library you can customize agents and build on top of it.
- **PremSQL API**: A self hosted API which can then be used using any language to make requests to use the deployed agents.
- **PremSQL Playground**: A playground UI (self hosted) which you can use interact with Text to SQL agents for your analysis tasks. You can also test your customized agents using this playground as well. Watch it in action.

https://github.com/user-attachments/assets/b6db9737-cd42-4848-8a44-f23a5de1f600

## News and blogs

- [Nov 18th 2024] [Prem-1B-SQL](https://huggingface.co/premai-io/prem-1B-SQL) reached 10K + downloads in HuggingFace 
- [Nov 7th 2024] Release of [Prem-1B-SQL Ollama](https://ollama.com/anindya/prem1b-sql-ollama-fp116) and Ollama support.
- [Nov 5th 2024] Release of PremSQL agents, AgentServer and Playground
- [Oct 30th] Prem-1B-SQL crossed 5K + downloads on Huggingface
- [Sep 20th 2024] First release of [Prem-1B-SQL](https://huggingface.co/premai-io/prem-1B-SQL) (51.54% on BirdBench private dataset) | [Blog post](https://blog.premai.io/prem-1b-sql-fully-local-performant-slm-for-text-to-sql/)
- [Sep 10th 2024] First release of PremSQL | [Blog Post](https://blog.premai.io/premsql-towards-end-to-end-local-text-to-sql-pipelines-2/)
- [Blog post]: [Using PremSQL to evaluate different open and closed source models](https://blog.premai.io/premsql-towards-end-to-end-local-text-to-sql-pipelines-2/)
- [Blog post]: [State of Text to SQL 2024](https://blog.premai.io/state-of-text2sql-2024/)

## 🚀 Features

- **Local-First**: Avoid third-party closed-source providers and keep your data secure.
- **Multiple connectors**: Supports [PremAI](https://app.premai.io/projects/), [Ollama](https://ollama.com/), [HuggingFace](https://huggingface.co/), [Apple MLX](https://huggingface.co/), [OpenAI](https://openai.com/).
- **Customizable Datasets**: Create, fine-tune, and evaluate models with built-in or custom datasets.
- **Robust Executors and Evaluators**: Easily connect to databases and assess model performance.
- **Advanced Generators**: Convert natural language prompts into executable SQL queries.
- **Error Handling and Self-Correction**: Automatically correct SQL queries during inference.
- **Fine-Tuning Support**: Fine-tune models with LoRA, QLoRA, or full fine-tuning strategies.
- **Agents**: Use PremSQL baseline agent to perform Text to SQL, write analysis reports and plot simple charts on databases.
- **Playground**: Use our playground to do the same for agents but with a better ChatGPT UI like experience dedicated for AI powered data analysis.
- **Importing CSVs or Kaggle CSV dataset directly to PremSQL playground**: You can analyse any CSV dataset from kaggle directly or from any folder using PremSQL.

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
    - [Agents](#agents)
    - [AgentServer and Playground](#playground)
  - [🤝 Contributing](#-contributing)
  - [🛣️ Roadmap](#️-roadmap)
  - [📝 License](#-license)

## 🛠️ Installation

PremSQL requires Python 3.8 or higher. Install the library via pip:

```bash
pip install -U premsql
```

## 🚀 Quickstart

Here’s a quick example of how to use PremSQL to generate SQL queries, plot charts and analyse dataframes all in natural language. You can name this file as `start_agent.py`

```python start_agent.py
import os
from dotenv import load_dotenv
from premsql.playground import AgentServer
from premsql.agents import BaseLineAgent
from premsql.generators import Text2SQLGeneratorPremAI
from premsql.executors import ExecutorUsingLangChain
from premsql.agents.tools import SimpleMatplotlibTool

load_dotenv()

text2sql_model = Text2SQLGeneratorPremAI(
    model_name="gpt-4o", experiment_name="text2sql_model", type="test",
    premai_api_key=os.environ.get("PREMAI_API_KEY"),
    project_id=os.environ.get("PREMAI_PROJECT_ID")
)

analyser_plotter_model = Text2SQLGeneratorPremAI(
    model_name="gpt-4o", experiment_name="text2sql_model", type="test",
    premai_api_key=os.environ.get("PREMAI_API_KEY"),
    project_id=os.environ.get("PREMAI_PROJECT_ID")
)

# Enter your Database path here. Supported SQLite, Postgres, MySQL and an unique session name.
db_connection_uri = "<sqlite:///db_path>"
session_name = "<session_name>"

agent = BaseLineAgent(
    session_name=session_name,
    db_connection_uri=db_connection_uri,
    specialized_model1=text2sql_model,
    specialized_model2=analyser_plotter_model,
    executor=ExecutorUsingLangChain(),
    auto_filter_tables=False,
    plot_tool=SimpleMatplotlibTool()
)

# Query the database
response = agent(
    "/query show me the phone numbers of direct charter-funded schools opened after 2000/1/1"
)

# Analyze the results
analysis = agent(
    "/analyse what patterns do you see in the data?"
)

# Create a visualization
plot = agent(
    "/plot create a bar chart showing school counts by year"
)
```

You can launch the PremSQL Playground (as shown in the above video by adding these two additional lines after instantiating Agent)

```python
agent_server = AgentServer(
    agent=agent,
    port={port},
    api_token=os.environ.get("PREMSQL_API_TOKEN")
)
agent_server.launch()
```

And then open two terminal. On one side write:

```bash
premsql launch all
```

and on the second side of the terminal write:

```bash
python start_agent.py
```

### Security Defaults

Recent hardening changes added safer defaults for Playground and AgentServer deployments:

- Playground session registration only accepts loopback AgentServer URLs such as `http://127.0.0.1:8100`.
- API authentication is supported through `PREMSQL_API_TOKEN`. When this variable is set, the Django backend, Playground clients, and FastAPI AgentServer all expect the same token.
- Generated SQL is now restricted to read-only queries. `INSERT`, `UPDATE`, `DELETE`, `DROP`, and similar statements are rejected by default.
- Direct raw SQL passthrough using backtick-wrapped prompts is disabled by default.
- CSV imports now enforce upload limits to reduce accidental or malicious resource exhaustion.

Recommended local environment variables:

```bash
export PREMSQL_API_TOKEN="change-this-token"
export PREMSQL_DJANGO_SECRET_KEY="change-this-secret"
export PREMSQL_ALLOWED_HOSTS="127.0.0.1,localhost"
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

### Agents

Agents has been quite popular for a while. Simply we can define agents as an orchestrated workflows between different LLMs/SLMs. PremSQL Agents are mainly focussed to execute tasks related to Databases. Breifly PremSQL agents can:

![](/assets/agent_flow.png)

- Query (`/query`) to a database from user’s natural language input.
- Analyse (`/analyse`) the database output and user query and give back a answer in natural language.
- Plot (`/plot`) basic charts based on user’s query.
- Lastly anything (`/followup`) which does not fit the above three categories, it can give you a followup on what do next.

PremSQL comes with a minimal agentic implementation (more implementation variants will come in later versions), which can query to a DB, provide analysis over dataframes and answer user questions and plot simple graphs. This is how you use our baseline Text to SQL agent.

```python
import os
from dotenv import load_dotenv
from premsql.playground import AgentServer
from premsql.agents import BaseLineAgent
from premsql.generators import Text2SQLGeneratorPremAI
from premsql.executors import ExecutorUsingLangChain
from premsql.agents.tools import SimpleMatplotlibTool

load_dotenv()

text2sql_model = Text2SQLGeneratorPremAI(
    model_name="gpt-4o", experiment_name="text2sql_model", type="test",
    premai_api_key=os.environ.get("PREMAI_API_KEY"),
    project_id=os.environ.get("PREMAI_PROJECT_ID")
)

analyser_plotter_model = Text2SQLGeneratorPremAI(
    model_name="gpt-4o", experiment_name="text2sql_model", type="test",
    premai_api_key=os.environ.get("PREMAI_API_KEY"),
    project_id=os.environ.get("PREMAI_PROJECT_ID")
)

# Enter your Database path here. Supported SQLite, Postgres, MySQL and an unique session name.
db_connection_uri = "<sqlite:///db_path>"
session_name = "<session_name>"

agent = BaseLineAgent(
    session_name=session_name,
    db_connection_uri=db_connection_uri,
    specialized_model1=text2sql_model,
    specialized_model2=analyser_plotter_model,
    executor=ExecutorUsingLangChain(),
    auto_filter_tables=False,
    plot_tool=SimpleMatplotlibTool()
)

# Query the database
response = agent(
    "/query show me the phone numbers of direct charter-funded schools opened after 2000/1/1"
)

# Analyze the results
analysis = agent(
    "/analyse what patterns do you see in the data?"
)

# Create a visualization
plot = agent(
    "/plot create a bar chart showing school counts by year"
)
```

You can learn more about PremSQL agents and their design patterns in details in [the documentation](https://docs.premai.io/premsql/introduction).

### Playground

You can think of Playground as a similar environment like chatGPT UI for specialized for RAGs on databases. There are different personas of usage of the PremSQL playground. To launch the Playground you need to write in the terminal:

```bash
premsql launch all
```

This will run two things:

- Django Backend API server (runing on port 8000)
- Streamlit UI which is our Playground.

In the above section you have see how we have defined our agent. You can deploy this agent anywhere using the AgentServer which is a fastapi wrapper. Using this you can either deploy as many instances of PremSQL Baseline agent or your own agent of your choice and connect it to the playground either to test it or use it for your internal database. Here is how you define your server and launch it.

```python
# File name: start_agent_server.py
import os
from premsql.playground import AgentServer
from premsql.agents import BaseLineAgent

# Define your agent as shown above:
agent = BaseLineAgent(...)

agent_server = AgentServer(
    agent=agent,
    port={port},
    api_token=os.environ.get("PREMSQL_API_TOKEN")
)
agent_server.launch()
```

Now inside another terminal write:

```bash
python start_agent_server.py
```

This can be any python file name. This will run a fastapi server. You need to paste a loopback url such as `http://127.0.0.1:8100` inside `Register New Session` in the UI. Below shows, how the basic backend architecture looks like on how Playground communicates with the server.

![](/assets/agent_server.png)

As you can see from the above architecture, you can create independent sessions using the starter script. You can do different levels of customization on this. For instance:

- You can use different generators and different models
- You can add your own DB executor
- Last but not the least, you can add a new worker or make your own agent using combination of our pre-existing worker implementations and your own logics.

So, you can add as many such agents with different customization or your own PremSQL compatible agents and test them and use them with PremSQL Playground. You can learn about more technical details in [the documentation](https://docs.premai.io/premsql/introduction).

## 🛣️ Roadmap

PremSQL is continuously evolving, with exciting features planned for future releases:

- **Synthesizer Component**: A tool to generate synthetic datasets from private data, enabling fully private text-to-SQL workflows and enhancing model fine-tuning capabilities.
- **Training Better Small Language Models**: Ongoing training and optimization of small language models specifically tailored to PremSQL’s unique requirements, ensuring efficient and effective performance in text-to-SQL tasks.
- **Optimization of Generators and Executors**: Improvements to enhance the robustness of existing components, including parallel processing to speed up generation and execution times.
- **Standard Tests and Stability Improvements**: Introduction of comprehensive tests for greater stability of the library and the planned rollout of a simple user interface to improve the overall user experience.

Stay tuned for these exciting updates! We encourage you to contribute and provide feedback to help us shape the future of PremSQL.

## 📝 License

PremSQL is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.

## ☘️ Citation

```
@misc{Anindyadeep2024PremSQL,
  author = {Anindyadeep},
  title = {PremSQL: End-to-End Local-First Text-to-SQL Pipelines},
  year = {2024},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/premAI-io/premsql}},
  note = {Accessed: 2024-12-10}
}
```
