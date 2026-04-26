from pathlib import Path
import yaml

from high_low_on_zillow.paths import CONFIG_DIR


def load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_settings() -> dict:
    return load_yaml(CONFIG_DIR / "settings.yaml")


def get_data_sources() -> dict:
    return load_yaml(CONFIG_DIR / "data_sources.yaml")