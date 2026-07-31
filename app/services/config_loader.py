from pathlib import Path
from typing import Any

import yaml

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"


class ConfigNotFoundError(Exception):
    def __init__(self, resource: str, state: str):
        self.resource = resource
        self.state = state
        super().__init__(f"No {resource} found for state '{state}'")


def _load_yaml(state: str, filename: str, resource: str) -> Any:
    path = CONFIG_DIR / state.lower() / filename
    if not path.is_file():
        raise ConfigNotFoundError(resource, state)

    with path.open() as f:
        return yaml.safe_load(f)


def load_questions(state: str) -> dict:
    return _load_yaml(state, "questions.yaml", resource="questions")


def load_rules(state: str) -> dict:
    return _load_yaml(state, "rules.yaml", resource="rules")


def load_rating(state: str) -> dict:
    return _load_yaml(state, "rating.yaml", resource="rating")
