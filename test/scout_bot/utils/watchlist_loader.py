# scout_bot/utils/watchlist_loader.py
import json
from pathlib import Path

def load_watchlist(path: str | Path) -> dict:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Watchlist not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    required = {"date", "phase", "largecap", "volume", "structure", "theme"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"Invalid watchlist format, missing: {missing}")

    return data
