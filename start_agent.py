"""
PremSQL Agent Server Startup Script

This script starts the AgentServer which handles text-to-SQL queries.
You need to configure an LLM provider (OpenAI, PremAI, vLLM, or Ollama).

Usage:
1. Set your API key in .env file
2. Run: python start_agent.py

Supported LLM Providers:
- vLLM (self-hosted models via OpenAI-compatible API)
- OpenAI (GPT-4, GPT-3.5, etc.)
- PremAI (Prem's hosted models)
- Ollama (local models)
- Custom (any OpenAI-compatible service)
"""

import os
import sys
import uuid
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from premsql.playground import AgentServer
from premsql.agents import BaseLineAgent
from premsql.executors import ExecutorUsingLangChain
from premsql.agents.tools import SimpleMatplotlibTool
from premsql.security import get_api_token

# Configuration
SESSION_NAME = os.environ.get("PREMSQL_SESSION_NAME", f"session_{uuid.uuid4().hex[:8]}")
DB_PATH = project_root / "sample_data" / "schools.db"
DB_CONNECTION_URI = f"sqlite:///{DB_PATH}"
PORT = int(os.environ.get("PREMSQL_AGENT_PORT", 8100))
# Get actual token (will auto-generate if not configured)
actual_token = get_api_token()

print(f"Database: {DB_CONNECTION_URI}")
print(f"Session: {SESSION_NAME}")
print(f"Port: {PORT}")


def create_vllm_agent():
    """Create agent using vLLM deployed model"""
    from premsql.generators import Text2SQLGeneratorVLLM

    # Support both old and new config names
    base_url = os.environ.get("VLLM_BASE_URL") or os.environ.get("VLLM_ENDPOINT")
    model_name = os.environ.get("VLLM_MODEL_NAME", "default")

    if not base_url:
        raise ValueError("VLLM_BASE_URL is required. Set it in .env file.")

    print(f"Using vLLM at: {base_url}")
    print(f"Model: {model_name}")

    text2sql_model = Text2SQLGeneratorVLLM(
        model_name=model_name,
        experiment_name="text2sql_vllm",
        type="test",
        base_url=base_url,
        # disable_thinking auto-detected for Qwen models
    )

    analyser_model = Text2SQLGeneratorVLLM(
        model_name=model_name,
        experiment_name="analyser_vllm",
        type="test",
        base_url=base_url,
    )

    return BaseLineAgent(
        session_name=SESSION_NAME,
        db_connection_uri=DB_CONNECTION_URI,
        specialized_model1=text2sql_model,
        specialized_model2=analyser_model,
        executor=ExecutorUsingLangChain(),
        auto_filter_tables=False,
        plot_tool=SimpleMatplotlibTool()
    )


def create_custom_agent():
    """Create agent using any OpenAI-compatible service"""
    from premsql.generators import Text2SQLGeneratorOpenAICompatible

    base_url = os.environ.get("CUSTOM_BASE_URL")
    model_name = os.environ.get("CUSTOM_MODEL_NAME", "default")
    api_key = os.environ.get("CUSTOM_API_KEY", "dummy-key")

    if not base_url:
        raise ValueError("CUSTOM_BASE_URL is required for custom provider.")

    print(f"Using custom service at: {base_url}")
    print(f"Model: {model_name}")

    # Optional: extra_body for service-specific parameters
    extra_body = None
    if os.environ.get("CUSTOM_DISABLE_THINKING", "").lower() == "true":
        extra_body = {"chat_template_kwargs": {"enable_thinking": False}}

    text2sql_model = Text2SQLGeneratorOpenAICompatible(
        model_name=model_name,
        experiment_name="text2sql_custom",
        type="test",
        base_url=base_url,
        api_key=api_key,
        extra_body=extra_body,
    )

    analyser_model = Text2SQLGeneratorOpenAICompatible(
        model_name=model_name,
        experiment_name="analyser_custom",
        type="test",
        base_url=base_url,
        api_key=api_key,
        extra_body=extra_body,
    )

    return BaseLineAgent(
        session_name=SESSION_NAME,
        db_connection_uri=DB_CONNECTION_URI,
        specialized_model1=text2sql_model,
        specialized_model2=analyser_model,
        executor=ExecutorUsingLangChain(),
        auto_filter_tables=False,
        plot_tool=SimpleMatplotlibTool()
    )


def create_openai_agent():
    """Create agent using OpenAI GPT model"""
    from premsql.generators import Text2SQLGeneratorOpenAI

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or api_key == "your-openai-api-key-here":
        raise ValueError("Please set OPENAI_API_KEY in .env file")

    model_name = os.environ.get("OPENAI_MODEL_NAME", "gpt-4o-mini")
    print(f"Using OpenAI model: {model_name}")

    text2sql_model = Text2SQLGeneratorOpenAI(
        model_name=model_name,
        experiment_name="text2sql_openai",
        type="test",
        openai_api_key=api_key
    )

    analyser_model = Text2SQLGeneratorOpenAI(
        model_name=model_name,
        experiment_name="analyser_openai",
        type="test",
        openai_api_key=api_key
    )

    return BaseLineAgent(
        session_name=SESSION_NAME,
        db_connection_uri=DB_CONNECTION_URI,
        specialized_model1=text2sql_model,
        specialized_model2=analyser_model,
        executor=ExecutorUsingLangChain(),
        auto_filter_tables=False,
        plot_tool=SimpleMatplotlibTool()
    )


def create_premai_agent():
    """Create agent using PremAI model"""
    from premsql.generators import Text2SQLGeneratorPremAI

    api_key = os.environ.get("PREMAI_API_KEY")
    project_id = os.environ.get("PREMAI_PROJECT_ID")

    if not api_key or api_key == "your-premai-api-key-here":
        raise ValueError("Please set PREMAI_API_KEY in .env file")

    model_name = os.environ.get("PREMAI_MODEL_NAME", "gpt-4o")
    print(f"Using PremAI model: {model_name}")

    text2sql_model = Text2SQLGeneratorPremAI(
        model_name=model_name,
        experiment_name="text2sql_premai",
        type="test",
        premai_api_key=api_key,
        project_id=project_id
    )

    analyser_model = Text2SQLGeneratorPremAI(
        model_name=model_name,
        experiment_name="analyser_premai",
        type="test",
        premai_api_key=api_key,
        project_id=project_id
    )

    return BaseLineAgent(
        session_name=SESSION_NAME,
        db_connection_uri=DB_CONNECTION_URI,
        specialized_model1=text2sql_model,
        specialized_model2=analyser_model,
        executor=ExecutorUsingLangChain(),
        auto_filter_tables=False,
        plot_tool=SimpleMatplotlibTool()
    )


def create_ollama_agent():
    """Create agent using Ollama local model"""
    from premsql.generators import Text2SQLGeneratorOllama

    base_url = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    model_name = os.environ.get("OLLAMA_MODEL_NAME", "llama3.2")

    print(f"Using Ollama at: {base_url}")
    print(f"Model: {model_name}")

    text2sql_model = Text2SQLGeneratorOllama(
        model_name=model_name,
        experiment_name="text2sql_ollama",
        type="test",
        base_url=base_url
    )

    analyser_model = Text2SQLGeneratorOllama(
        model_name=model_name,
        experiment_name="analyser_ollama",
        type="test",
        base_url=base_url
    )

    return BaseLineAgent(
        session_name=SESSION_NAME,
        db_connection_uri=DB_CONNECTION_URI,
        specialized_model1=text2sql_model,
        specialized_model2=analyser_model,
        executor=ExecutorUsingLangChain(),
        auto_filter_tables=False,
        plot_tool=SimpleMatplotlibTool()
    )


def detect_provider():
    """Auto-detect which LLM provider is configured"""
    providers = []

    # Check vLLM
    if os.environ.get("VLLM_BASE_URL"):
        providers.append(("vllm", "vLLM"))

    # Check Custom OpenAI-compatible
    if os.environ.get("CUSTOM_BASE_URL"):
        providers.append(("custom", "Custom OpenAI-compatible"))

    # Check OpenAI
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    if openai_key and openai_key != "your-openai-api-key-here":
        providers.append(("openai", "OpenAI"))

    # Check PremAI
    premai_key = os.environ.get("PREMAI_API_KEY", "")
    if premai_key and premai_key != "your-premai-api-key-here":
        providers.append(("premai", "PremAI"))

    # Check Ollama (always available if installed)
    providers.append(("ollama", "Ollama"))

    return providers


def main():
    # Detect available providers
    providers = detect_provider()

    if len(providers) == 1 and providers[0][0] == "ollama":
        # Only Ollama available, check if it's actually running
        print("=" * 60)
        print("No external LLM provider configured.")
        print("=" * 60)
        print("\nConfigure one of the following in .env file:")
        print("  1. VLLM_BASE_URL + VLLM_MODEL_NAME - for vLLM deployments")
        print("  2. CUSTOM_BASE_URL + CUSTOM_MODEL_NAME - for any OpenAI-compatible service")
        print("  3. OPENAI_API_KEY + OPENAI_MODEL_NAME - for OpenAI GPT models")
        print("  4. PREMAI_API_KEY + PREMAI_PROJECT_ID - for PremAI")
        print("\nOr use Ollama locally: https://ollama.com")
        print("=" * 60)
        sys.exit(1)

    # Use first configured provider (priority order)
    provider_type, provider_name = providers[0]
    print(f"Using {provider_name} as LLM provider")

    # Create agent based on provider
    creators = {
        "vllm": create_vllm_agent,
        "custom": create_custom_agent,
        "openai": create_openai_agent,
        "premai": create_premai_agent,
        "ollama": create_ollama_agent,
    }

    agent = creators[provider_type]()

    # Start AgentServer
    print(f"\nStarting AgentServer on port {PORT}...")
    is_dev_token = not os.environ.get("PREMSQL_API_TOKEN")
    if is_dev_token:
        print(f"API Token (auto-generated): {actual_token}")
    else:
        print(f"API Token: [configured]")
    print(f"\nURL: http://127.0.0.1:{PORT}")
    print("=" * 60)

    agent_server = AgentServer(
        agent=agent,
        url="localhost",
        port=PORT,
        api_token=None  # Let AgentServer handle token internally
    )

    agent_server.launch()


if __name__ == "__main__":
    main()