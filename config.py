import sys
import os

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

_config: dict | None = None


def load_config(path: str = "config.toml") -> dict:
    global _config
    if not os.path.exists(path):
        _config = {
            "database": {
                "type": "sqlite",
                "sqlite": {"path": "sentences.db"},
            }
        }
        return _config
    with open(path, "rb") as f:
        _config = tomllib.load(f)
    return _config


def get_config() -> dict:
    if _config is None:
        load_config()
    return _config


def get_db_config() -> dict:
    return get_config()["database"]
