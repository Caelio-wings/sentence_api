import sys
import os

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

_config: dict | None = None


def load_config(path: str | None = None) -> dict:
    global _config
    candidates = [path] if path else ["config.toml", "config/config.toml"]
    for p in candidates:
        if p and os.path.exists(p):
            with open(p, "rb") as f:
                _config = tomllib.load(f)
            return _config
    _config = {
        "database": {
            "type": "sqlite",
            "sqlite": {"path": "sentences.db"},
        }
    }
    return _config


def get_config() -> dict:
    if _config is None:
        load_config()
    return _config


def get_db_config() -> dict:
    return get_config()["database"]


def get_server_config() -> dict:
    cfg = get_config().get("server", {})
    return {
        "host": cfg.get("host", "0.0.0.0"),
        "port": cfg.get("port", 8000),
    }
