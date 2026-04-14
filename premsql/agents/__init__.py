from importlib import import_module

__all__ = ["BaseLineAgent", "AgentInteractionMemory"]


def __getattr__(name):
    if name == "BaseLineAgent":
        return import_module("premsql.agents.baseline.main").BaseLineAgent
    if name == "AgentInteractionMemory":
        return import_module("premsql.agents.memory").AgentInteractionMemory
    raise AttributeError(f"module 'premsql.agents' has no attribute {name!r}")
