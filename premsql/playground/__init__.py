from importlib import import_module

__all__ = ["AgentServer", "InferenceServerAPIClient", "BackendAPIClient"]


def __getattr__(name):
    mapping = {
        "BackendAPIClient": (
            "premsql.playground.backend.backend_client",
            "BackendAPIClient",
        ),
        "InferenceServerAPIClient": (
            "premsql.playground.inference_server.api_client",
            "InferenceServerAPIClient",
        ),
        "AgentServer": ("premsql.playground.inference_server.service", "AgentServer"),
    }
    if name not in mapping:
        raise AttributeError(f"module 'premsql.playground' has no attribute {name!r}")
    module_name, attr_name = mapping[name]
    return getattr(import_module(module_name), attr_name)
