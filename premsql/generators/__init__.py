from importlib import import_module

__all__ = [
    "Text2SQLGeneratorHF",
    "Text2SQLGeneratorPremAI",
    "Text2SQLGeneratorOpenAI",
    "Text2SQLGeneratorMLX",
    "Text2SQLGeneratorOllama",
    "Text2SQLGeneratorVLLM",
    "Text2SQLGeneratorOpenAICompatible",
]


def __getattr__(name):
    mapping = {
        "Text2SQLGeneratorHF": ("premsql.generators.huggingface", "Text2SQLGeneratorHF"),
        "Text2SQLGeneratorPremAI": ("premsql.generators.premai", "Text2SQLGeneratorPremAI"),
        "Text2SQLGeneratorOpenAI": ("premsql.generators.openai", "Text2SQLGeneratorOpenAI"),
        "Text2SQLGeneratorMLX": ("premsql.generators.mlx", "Text2SQLGeneratorMLX"),
        "Text2SQLGeneratorOllama": ("premsql.generators.ollama_model", "Text2SQLGeneratorOllama"),
        "Text2SQLGeneratorVLLM": ("premsql.generators.vllm", "Text2SQLGeneratorVLLM"),
        "Text2SQLGeneratorOpenAICompatible": (
            "premsql.generators.openai_compatible",
            "Text2SQLGeneratorOpenAICompatible",
        ),
    }
    if name not in mapping:
        raise AttributeError(f"module 'premsql.generators' has no attribute {name!r}")
    module_name, attr_name = mapping[name]
    return getattr(import_module(module_name), attr_name)