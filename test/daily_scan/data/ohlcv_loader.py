import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent / "ohlcv"


def load_daily_ohlcv(symbol: str, date: str) -> dict:
    file_path = BASE_DIR / f"{symbol}.csv"

    if not file_path.exists():
        raise FileNotFoundError(f"OHLCV file not found: {file_path}")

    with open(file_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["date"] == date:
                close = int(row["close"])
                volume = int(row["volume"])
                return {
                    "open": int(row["open"]),
                    "high": int(row["high"]),
                    "low": int(row["low"]),
                    "close": close,
                    "volume": volume,
                    "trading_value": close * volume,
                }

    raise ValueError(f"No OHLCV data for {symbol} on {date}")


def load_volume_history(symbol: str, days: int) -> list[int]:
    file_path = BASE_DIR / f"{symbol}.csv"

    if not file_path.exists():
        raise FileNotFoundError(f"OHLCV file not found: {file_path}")

    volumes = []

    with open(file_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            volumes.append(int(row["volume"]))

    return volumes[:days]
