"""
OpenAI Generator for PremSQL

This generator uses the official OpenAI API for text-to-SQL generation.
Supports GPT-4, GPT-3.5, and other OpenAI models.

For OpenAI-compatible services (vLLM, LM Studio, etc.), use:
- Text2SQLGeneratorVLLM for vLLM deployments
- Text2SQLGeneratorOpenAICompatible for any OpenAI-compatible API
"""

import os
from typing import Optional

from premsql.generators.base import Text2SQLGeneratorBase

try:
    from openai import OpenAI
except ImportError:
    raise ImportError("Module openai is not installed. Run: pip install openai")


class Text2SQLGeneratorOpenAI(Text2SQLGeneratorBase):
    """
    Generator using official OpenAI API.

    Environment Variables:
        OPENAI_API_KEY: Your OpenAI API key (required)
        OPENAI_BASE_URL: Optional custom base URL (for proxies)
        OPENAI_ORG_ID: Optional organization ID
    """

    def __init__(
        self,
        model_name: str,
        experiment_name: str,
        type: str,
        experiment_folder: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        organization: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize OpenAI generator.

        Args:
            model_name: OpenAI model name (e.g., "gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo")
            experiment_name: Name for this experiment
            type: Experiment type (e.g., "test", "train")
            experiment_folder: Custom folder for experiment results
            openai_api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            base_url: Custom base URL (optional, for proxies)
            organization: OpenAI organization ID (optional)
            **kwargs: Additional arguments
        """
        self._api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        self._base_url = base_url or os.environ.get("OPENAI_BASE_URL")
        self._organization = organization or os.environ.get("OPENAI_ORG_ID")
        self._kwargs = kwargs

        if not self._api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable "
                "or pass openai_api_key parameter."
            )

        self.model_name = model_name
        super().__init__(
            experiment_folder=experiment_folder,
            experiment_name=experiment_name,
            type=type,
        )

    @property
    def load_client(self):
        """Load OpenAI client"""
        client_kwargs = {"api_key": self._api_key}
        if self._base_url:
            client_kwargs["base_url"] = self._base_url
        if self._organization:
            client_kwargs["organization"] = self._organization
        return OpenAI(**client_kwargs)

    @property
    def load_tokenizer(self):
        """Tokenizer not needed for OpenAI API"""
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
        Generate SQL using OpenAI API.

        Args:
            data_blob: Contains 'prompt' key with the input prompt
            temperature: Sampling temperature (0.0 = deterministic)
            max_new_tokens: Maximum tokens to generate
            postprocess: Whether to postprocess output as SQL
            **kwargs: Additional generation parameters
        """
        prompt = data_blob["prompt"]
        generation_config = {
            **kwargs,
            **{"temperature": temperature, "max_tokens": max_new_tokens},
        }

        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            **generation_config
        ).choices[0].message.content

        return self.postprocess(output_string=completion) if postprocess else completion