import yaml
from pathlib import Path


DEFAULT_CONFIG_PATH = Path("config.yaml")


def load_config():
    if not DEFAULT_CONFIG_PATH.exists():
        return {}

    try:
        with DEFAULT_CONFIG_PATH.open("r") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}
