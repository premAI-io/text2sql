from importlib import import_module

__all__ = ["ExecutorUsingLangChain", "SQLiteExecutor", "OptimizedSQLiteExecutor"]


def __getattr__(name):
    mapping = {
        "ExecutorUsingLangChain": (
            "premsql.executors.from_langchain",
            "ExecutorUsingLangChain",
        ),
        "SQLiteExecutor": ("premsql.executors.from_sqlite", "SQLiteExecutor"),
        "OptimizedSQLiteExecutor": (
            "premsql.executors.from_sqlite",
            "OptimizedSQLiteExecutor",
        ),
    }
    if name not in mapping:
        raise AttributeError(f"module 'premsql.executors' has no attribute {name!r}")
    module_name, attr_name = mapping[name]
    return getattr(import_module(module_name), attr_name)
