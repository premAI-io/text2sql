"""
vLLM Generator for PremSQL

vLLM provides an OpenAI-compatible API server, making it easy to integrate
with PremSQL. This generator handles vLLM-specific configurations like
disable_thinking for Qwen3 models.

Usage:
    # Start vLLM server first:
    vllm serve /models/qwen --port 8000

    # Then use in PremSQL:
    from premsql.generators import Text2SQLGeneratorVLLM

    generator = Text2SQLGeneratorVLLM(
        model_name="/models/qwen",
        base_url="http://localhost:8000/v1",
        experiment_name="text2sql_vllm",
        type="test"
    )
"""

import os
from typing import Optional

from premsql.generators.base import Text2SQLGeneratorBase
from premsql.logger import setup_console_logger

logger = setup_console_logger(name="[VLLM-GENERATOR]")

try:
    from openai import OpenAI
except ImportError:
    raise ImportError("Module openai is not installed. Run: pip install openai")


class Text2SQLGeneratorVLLM(Text2SQLGeneratorBase):
    """
    Generator for vLLM deployed models.

    vLLM is a high-performance LLM inference server that provides an
    OpenAI-compatible API. This generator supports:

    - Any model deployed via vLLM
    - Qwen3 thinking mode control (disable_thinking)
    - Custom base_url for remote vLLM servers

    Environment Variables:
        VLLM_BASE_URL: Base URL for vLLM server (e.g., http://localhost:8000/v1)
        VLLM_MODEL_NAME: Model name/path as configured in vLLM
        VLLM_API_KEY: Optional API key (vLLM doesn't require real key by default)
    """

    def __init__(
        self,
        model_name: str,
        experiment_name: str,
        type: str,
        experiment_folder: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        disable_thinking: Optional[bool] = None,
        extra_params: Optional[dict] = None,
        **kwargs
    ):
        """
        Initialize vLLM generator.

        Args:
            model_name: Model name or path as configured in vLLM serve command
            experiment_name: Name for this experiment
            type: Experiment type (e.g., "test", "train")
            experiment_folder: Custom folder for experiment results
            base_url: vLLM server URL (e.g., http://localhost:8000/v1)
            api_key: API key (optional, vLLM doesn't require real key)
            disable_thinking: Disable Qwen3 thinking mode (auto-detect for Qwen models)
            extra_params: Additional parameters to pass to vLLM API
        """
        self._base_url = base_url or os.environ.get("VLLM_BASE_URL")
        self._api_key = api_key or os.environ.get("VLLM_API_KEY") or "vllm-dummy-key"
        self._extra_params = extra_params or {}
        self._kwargs = kwargs

        # Auto-detect if thinking mode should be disabled for Qwen models
        if disable_thinking is None:
            disable_thinking = self._is_qwen_model(model_name)
        self._disable_thinking = disable_thinking

        self.model_name = model_name
        super().__init__(
            experiment_folder=experiment_folder,
            experiment_name=experiment_name,
            type=type,
        )

        logger.info(f"vLLM generator initialized with base_url: {self._base_url}")
        if self._disable_thinking:
            logger.info("Qwen thinking mode disabled")

    def _is_qwen_model(self, model_name: str) -> bool:
        """Auto-detect if model is Qwen3 which needs thinking mode disabled"""
        qwen_patterns = ["qwen", "Qwen", "QWEN"]
        return any(pattern.lower() in model_name.lower() for pattern in qwen_patterns)

    @property
    def load_client(self):
        """Load OpenAI client configured for vLLM"""
        if not self._base_url:
            raise ValueError(
                "vLLM base_url is required. Set VLLM_BASE_URL environment variable "
                "or pass base_url parameter."
            )
        return OpenAI(api_key=self._api_key, base_url=self._base_url)

    @property
    def load_tokenizer(self):
        """vLLM doesn't need tokenizer, handled server-side"""
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
        Generate SQL using vLLM.

        Args:
            data_blob: Contains 'prompt' key with the input prompt
            temperature: Sampling temperature
            max_new_tokens: Maximum tokens to generate
            postprocess: Whether to postprocess output as SQL
            **kwargs: Additional generation parameters
        """
        prompt = data_blob["prompt"]
        generation_config = {
            "temperature": temperature,
            "max_tokens": max_new_tokens,
            **self._extra_params,
            **kwargs,
        }

        # For Qwen3 models, disable thinking mode via extra_body
        extra_body = None
        if self._disable_thinking:
            extra_body = {"chat_template_kwargs": {"enable_thinking": False}}

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                extra_body=extra_body,
                **generation_config
            )
            output = response.choices[0].message.content
        except Exception as e:
            logger.error(f"vLLM generation error: {e}")
            raise

        return self.postprocess(output_string=output) if postprocess else output