import yaml
from pathlib import Path


DEFAULT_CONFIG_PATH = Path("config.yaml")
DEFAULT_STRATEGY_CONFIG_PATH = Path("strategy_config.yaml")


def _load_yaml_file(path):
    if not path.exists():
        return {}

    try:
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def load_config():
    return _load_yaml_file(DEFAULT_CONFIG_PATH)


def load_strategy_config():
    data = _load_yaml_file(DEFAULT_STRATEGY_CONFIG_PATH)

    if isinstance(data, dict) and isinstance(data.get("strategies"), dict):
        return data["strategies"]

    return data if isinstance(data, dict) else {}
