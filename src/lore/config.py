"""Configuration management for Lore."""

import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

from lore.core.exceptions import ConfigError
from lore.core.models import LoreConfig


def get_lore_home() -> Path:
    """Returns the root directory for Lore user data."""
    custom_home = os.environ.get("LORE_HOME")
    if custom_home:
        path = Path(custom_home).expanduser().resolve()
    else:
        path = Path.home() / ".lore"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_config_path() -> Path:
    """Returns the path to the config YAML file."""
    return get_lore_home() / "config.yml"


def load_config() -> LoreConfig:
    """Loads configuration from ~/.lore/config.yml or creates default."""
    config_file = get_config_path()
    if not config_file.exists():
        default_cfg = LoreConfig()
        save_config(default_cfg)
        return default_cfg

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return LoreConfig(**data)
    except Exception as e:
        raise ConfigError(f"Failed to parse config file at {config_file}: {e}") from e


def save_config(config: LoreConfig) -> None:
    """Saves the LoreConfig object to ~/.lore/config.yml."""
    config_file = get_config_path()
    try:
        data = config.model_dump(mode="json")
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
    except Exception as e:
        raise ConfigError(f"Failed to write config file to {config_file}: {e}") from e


def update_config(updates: Dict[str, Any]) -> LoreConfig:
    """Updates selected keys in configuration and persists to disk."""
    current = load_config()
    data = current.model_dump()
    for k, v in updates.items():
        if k in data:
            data[k] = v
        else:
            raise ConfigError(f"Unknown configuration key: {k}")
    updated = LoreConfig(**data)
    save_config(updated)
    return updated
