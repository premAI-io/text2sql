"""
OpenAI-Compatible Generator for PremSQL

This generator supports any service that provides an OpenAI-compatible API,
including:
- vLLM
- LM Studio
- LocalAI
- Oobabooga (with OpenAI extension)
- Text Generation WebUI
- Any custom deployment with OpenAI-compatible endpoints

Usage:
    from premsql.generators import Text2SQLGeneratorOpenAICompatible

    # For vLLM
    generator = Text2SQLGeneratorOpenAICompatible(
        model_name="/models/qwen",
        base_url="http://localhost:8000/v1",
        experiment_name="text2sql_custom",
        type="test"
    )

    # For LM Studio
    generator = Text2SQLGeneratorOpenAICompatible(
        model_name="local-model",
        base_url="http://localhost:1234/v1",
        experiment_name="lm_studio",
        type="test"
    )

    # For any custom OpenAI-compatible service
    generator = Text2SQLGeneratorOpenAICompatible(
        model_name="your-model",
        base_url="http://your-server:port/v1",
        api_key="your-key-if-needed",
        experiment_name="custom",
        type="test",
        extra_body={"custom_param": "value"}  # Service-specific params
    )
"""

import os
from typing import Optional

from premsql.generators.base import Text2SQLGeneratorBase
from premsql.logger import setup_console_logger

logger = setup_console_logger(name="[OPENAI-COMPATIBLE-GENERATOR]")

try:
    from openai import OpenAI
except ImportError:
    raise ImportError("Module openai is not installed. Run: pip install openai")


class Text2SQLGeneratorOpenAICompatible(Text2SQLGeneratorBase):
    """
    Universal generator for any OpenAI-compatible API service.

    This generator provides a flexible interface for services that implement
    the OpenAI chat completions API, allowing you to use:
    - Self-hosted models (vLLM, LM Studio, LocalAI)
    - Custom deployments
    - Alternative API providers

    The generator supports:
    - Custom base_url for any OpenAI-compatible endpoint
    - Optional API key (some services don't require authentication)
    - extra_body for service-specific parameters
    - extra_headers for custom headers
    - Model-specific configurations via extra_params
    """

    def __init__(
        self,
        model_name: str,
        experiment_name: str,
        type: str,
        experiment_folder: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        extra_body: Optional[dict] = None,
        extra_headers: Optional[dict] = None,
        default_params: Optional[dict] = None,
        **kwargs
    ):
        """
        Initialize OpenAI-compatible generator.

        Args:
            model_name: Model identifier as expected by the service
            experiment_name: Name for this experiment
            type: Experiment type (e.g., "test", "train")
            experiment_folder: Custom folder for experiment results
            base_url: API endpoint URL (e.g., http://localhost:8000/v1)
            api_key: API key (optional for local deployments)
            extra_body: Additional body parameters for API requests
                       (e.g., {"chat_template_kwargs": {"enable_thinking": False}})
            extra_headers: Additional headers for API requests
            default_params: Default generation parameters (temperature, etc.)
            **kwargs: Additional arguments passed to base class
        """
        # Get configuration from environment if not provided
        self._base_url = base_url or os.environ.get("OPENAI_COMPATIBLE_BASE_URL")
        self._api_key = api_key or os.environ.get("OPENAI_COMPATIBLE_API_KEY") or "compatible-dummy-key"
        self._extra_body = extra_body or {}
        self._extra_headers = extra_headers or {}
        self._default_params = default_params or {}
        self._kwargs = kwargs

        self.model_name = model_name
        super().__init__(
            experiment_folder=experiment_folder,
            experiment_name=experiment_name,
            type=type,
        )

        if self._base_url:
            logger.info(f"OpenAI-compatible generator initialized: {self._base_url}")
        else:
            logger.warning(
                "No base_url provided. Will use OpenAI's default API. "
                "Set base_url or OPENAI_COMPATIBLE_BASE_URL environment variable."
            )

    @property
    def load_client(self):
        """Load OpenAI client with custom configuration"""
        client_kwargs = {"api_key": self._api_key}
        if self._base_url:
            client_kwargs["base_url"] = self._base_url
        if self._extra_headers:
            client_kwargs["default_headers"] = self._extra_headers
        return OpenAI(**client_kwargs)

    @property
    def load_tokenizer(self):
        """Tokenizer not needed for API-based generators"""
        pass

    @property
    def model_name_or_path(self):
        return self.model_name

    def generate(
        self,
        data_blob: dict,
        temperature: Optional[float] = 0.0,
        max_new_tokens: Optional[int] = 256,
        postprocess: Optional[bool] = True,
        **kwargs
    ) -> str:
        """
        Generate SQL using the OpenAI-compatible API.

        Args:
            data_blob: Contains 'prompt' key with the input prompt
            temperature: Sampling temperature (0.0 = deterministic)
            max_new_tokens: Maximum tokens to generate
            postprocess: Whether to postprocess output as SQL
            **kwargs: Additional generation parameters
        """
        prompt = data_blob["prompt"]

        # Merge default params with call-specific params
        generation_config = {
            "temperature": temperature,
            "max_tokens": max_new_tokens,
            **self._default_params,
            **kwargs,
        }

        # Prepare API call options
        api_options = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            **generation_config,
        }

        # Add extra_body if provided
        if self._extra_body:
            api_options["extra_body"] = self._extra_body

        try:
            response = self.client.chat.completions.create(**api_options)
            output = response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI-compatible generation error: {e}")
            raise

        return self.postprocess(output_string=output) if postprocess else output

    def set_extra_body(self, extra_body: dict):
        """Update extra_body parameters dynamically"""
        self._extra_body.update(extra_body)
        logger.info(f"Updated extra_body: {self._extra_body}")

    def set_default_params(self, params: dict):
        """Update default generation parameters"""
        self._default_params.update(params)
        logger.info(f"Updated default_params: {self._default_params}")