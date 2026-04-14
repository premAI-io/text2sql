import random
import streamlit as st
from typing import Tuple, Optional
from pathlib import Path
from premsql.playground.frontend.utils import (
    download_from_kaggle,
    migrate_from_csv_to_sqlite,
    _is_valid_kaggle_id,
    migrate_local_csvs_to_sqlite
)

COMMON = """
db_connection_uri = "sqlite:///{db_path}"
baseline = BaseLineAgent(
    session_name="{session_name}",                # An unique session name must be put
    db_connection_uri=db_connection_uri,        # DB which needs to connect for Text to SQL 
    specialized_model1=text2sql_model,          # This referes to the Text to SQL model
    specialized_model2=analyser_plotter_model,  # This refers to any model other than Text to SQL
    executor=ExecutorUsingLangChain(),          # Which DB executor to use
    auto_filter_tables=False,                   # Whether to filter tables before Text to SQL
    plot_tool=SimpleMatplotlibTool()            # Matplotlib Tool which will be used by plotter worker
)

agent_server = AgentServer(
    agent=baseline,
    port={port},
    api_token=os.environ.get("PREMSQL_API_TOKEN")
)
agent_server.launch()
"""

STARTER_CODE_FILE_MLX = """
import os
from premsql.playground import AgentServer
from premsql.agents import BaseLineAgent
from premsql.generators import Text2SQLGeneratorMLX
from premsql.executors import ExecutorUsingLangChain
from premsql.agents.tools import SimpleMatplotlibTool
text2sql_model = Text2SQLGeneratorMLX(
    model_name_or_path="premai-io/prem-1B-SQL", experiment_name="text2sql_model", type="test"
)

analyser_plotter_model = Text2SQLGeneratorMLX(
    model_name_or_path="meta-llama/Llama-3.2-1B-Instruct", experiment_name="analyser_model", type="test",
)
"""


STARTER_CODE_FILE_OLLAMA = """
import os
from premsql.playground import AgentServer
from premsql.agents import BaseLineAgent
from premsql.generators import Text2SQLGeneratorOllama
from premsql.agents.tools import SimpleMatplotlibTool
from premsql.executors import ExecutorUsingLangChain

text2sql_model = Text2SQLGeneratorOllama(
    model_name="anindya/prem1b-sql-ollama-fp116",
    experiment_name="ollama",
    type="test"
)

analyser_plotter_model = Text2SQLGeneratorOllama(
    model_name="llama3.2:1b",
    experiment_name="ollama",
    type="test"
)
"""


STARTER_CODE_FILE_HF = """
import os
from premsql.playground import AgentServer
from premsql.agents import BaseLineAgent
from premsql.generators import Text2SQLGeneratorHF
from premsql.executors import ExecutorUsingLangChain
from premsql.agents.tools import SimpleMatplotlibTool

text2sql_model = Text2SQLGeneratorHF(
    model_name_or_path="premai-io/prem-1B-SQL", experiment_name="text2sql_model", type="test"
)

analyser_plotter_model = Text2SQLGeneratorHF(
    model_name_or_path="meta-llama/Llama-3.2-1B-Instruct", experiment_name="analyser_model", type="test",
)
"""

STARTER_CODE_FILE_PREMAI = """
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
    model_name="gpt-4o", experiment_name="analyser_plotter_model", type="test",
    premai_api_key=os.environ.get("PREMAI_API_KEY"),
    project_id=os.environ.get("PREMAI_PROJECT_ID")
)
"""

STARTER_CODE_FILE_OPENAI = """
import os
from dotenv import load_dotenv
from premsql.playground import AgentServer
from premsql.agents import BaseLineAgent
from premsql.generators import Text2SQLGeneratorOpenAI
from premsql.executors import ExecutorUsingLangChain
from premsql.agents.tools import SimpleMatplotlibTool

load_dotenv()

text2sql_model = Text2SQLGeneratorOpenAI(
    model_name="gpt-4o", experiment_name="text2sql_model", type="test",
    openai_api_key=os.environ.get("OPENAI_API_KEY")
)

analyser_plotter_model = Text2SQLGeneratorOpenAI(
    model_name="gpt-4o", experiment_name="analyser_and_plotter_model", type="test",
    openai_api_key=os.environ.get("OPENAI_API_KEY")
)
"""

def render_starter_code(session_name, db_path):
    with st.expander(label="Start Locally with MLX", expanded=True):
        st.warning("Ensure you have mlx installed and using inside mac device.")
        st.info("Python PyPI: pip install mlx mlx-lm")

        code = (STARTER_CODE_FILE_MLX + COMMON).format(
            session_name=session_name, 
            db_path=db_path,
            port=random.choice(range(7000, 9000))
        )
        st.code(code, language="python")
    
    with st.expander(label="Start Locally with HuggingFace"):
        st.warning("Ensure you have torch, transformers installed inside your device.")
        st.info("Python PyPI: pip install torch transformers")

        code = (STARTER_CODE_FILE_HF + COMMON).format(
            session_name=session_name, 
            db_path=db_path,
            port=random.choice(range(7000, 9000))
        )
        st.code(code, language="python")

    with st.expander(label="Start Locally with Ollama"):
        st.warning("Ensure you have ollama installed inside your device.")
        st.info("Python PyPI: pip install ollama")
        st.info("Install Ollama: curl -fsSL https://ollama.com/install.sh | sh")

        code = (STARTER_CODE_FILE_OLLAMA + COMMON).format(
            session_name=session_name, 
            db_path=db_path,
            port=random.choice(range(7000, 9000))
        )
        st.code(code, language="python")

    with st.expander(label="Start with PremAI"):
        code = (STARTER_CODE_FILE_PREMAI + COMMON).format(
            session_name=session_name, 
            db_path=db_path,
            port=random.choice(range(7000, 9000))
        )
        st.code(code, language="python")

    with st.expander(label="Start with OpenAI"):
        code = (STARTER_CODE_FILE_OPENAI + COMMON).format(
            session_name=session_name, 
            db_path=db_path,
            port=random.choice(range(7000, 9000))
        )
        st.code(code, language="python")


class UploadComponent:
    @staticmethod
    def render_kaggle_view() -> Tuple[Optional[str], Optional[Path]]:
        session_name = None
        sqlite_db_path = None
        
        with st.sidebar:
            with st.expander(label="Upload From Kaggle"):
                with st.form(key="kaggle", clear_on_submit=True):
                    session_name = st.text_input(label="Enter session name")
                    kaggle_id = st.text_input(label="Enter kaggle id")
                    submit = st.form_submit_button(label="Submit")
                    
                    if submit:
                        if not session_name:
                            st.error("Please enter a session name")
                            return None, None

                        if not _is_valid_kaggle_id(kaggle_id):
                            st.error("Invalid Kaggle Id")
                            return None, None
                        
                        try:
                            with st.spinner(text="Downloading from Kaggle"):
                                path = download_from_kaggle(kaggle_dataset_id=kaggle_id)
                            
                            sqlite_db_path = migrate_from_csv_to_sqlite(
                                folder_containing_csvs=path, 
                                session_name=session_name
                            )
                            st.success("Files downloaded and processed successfully!")
                        except Exception as e:
                            st.error(f"Error processing files: {str(e)}")
        if session_name and sqlite_db_path:
            render_starter_code(
                session_name=session_name, db_path=sqlite_db_path
            )
                    

    @staticmethod
    def render_csv_upload_view() -> Tuple[Optional[str], Optional[Path]]:
        with st.sidebar:
            with st.expander(label="Upload CSV Files"):
                with st.form(key="csv_upload", clear_on_submit=True):
                    session_name = st.text_input(label="Enter session name")
                    uploaded_files = st.file_uploader(
                        label="Upload CSV files",
                        type="csv",
                        accept_multiple_files=True
                    )
                    submit = st.form_submit_button(label="Submit")
                    
                    if submit:
                        if not session_name:
                            st.error("Please enter a session name")
                            return None, None

                        if not uploaded_files:
                            st.error("Please upload at least one CSV file")
                            return None, None
                        
                        try:
                            with st.spinner(text="Processing CSV files"):
                                sqlite_db_path = migrate_local_csvs_to_sqlite(
                                    uploaded_files=uploaded_files,
                                    session_name=session_name
                                )
                            st.success("Files uploaded and processed successfully!")
                            
                        except Exception as e:
                            st.error(f"Error processing files: {str(e)}")
        if session_name and sqlite_db_path:
            render_starter_code(
                session_name=session_name, db_path=sqlite_db_path
            )
                    
    

    
