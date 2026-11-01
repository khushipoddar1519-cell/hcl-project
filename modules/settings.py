"""Tiny JSON-backed settings + 'remember me' storage."""
import json
from . import config


def load():
    data = dict(config.DEFAULT_SETTINGS)
    try:
        if config.SETTINGS_JSON.exists():
            data.update(json.loads(config.SETTINGS_JSON.read_text()))
    except Exception:
        pass
    return data


def save(values: dict):
    data = load()
    data.update(values)
    config.SETTINGS_JSON.write_text(json.dumps(data, indent=2))
    return data


def get_remembered() -> str:
    try:
        if config.REMEMBER_JSON.exists():
            return json.loads(config.REMEMBER_JSON.read_text()).get("username", "")
    except Exception:
        pass
    return ""


def set_remembered(username: str | None):
    try:
        if username:
            config.REMEMBER_JSON.write_text(json.dumps({"username": username}))
        elif config.REMEMBER_JSON.exists():
            config.REMEMBER_JSON.unlink()
    except Exception:
        pass
