import json
import os
from pathlib import Path

def _get_config_dir() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path.home() / ".config"
    config_dir = base / "NewsPilot"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir

def _get_license_file() -> Path:
    return _get_config_dir() / "license.json"

def save_license_key(license_key: str) -> None:
    with open(_get_license_file(), "w", encoding="utf-8") as f:
        json.dump({"license_key": license_key}, f)

def load_license_key() -> str | None:
    path = _get_license_file()
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("license_key")
    except (json.JSONDecodeError, OSError):
        return None

def clear_license_key() -> None:
    path = _get_license_file()
    if path.exists():
        path.unlink()