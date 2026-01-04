from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from selector import (
    SelectorConfig,
    select_watchlist,
)

# =========================
# Paths
# =========================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# =========================
# Phase Auto Switch
# =========================

def infer_phase(df: pd.DataFrame, lookback: int = 20) -> str:
    max_days = (
        df.groupby("symbol")["date"]
        .nunique()
        .max()
    )
    return "normal" if max_days >= lookback else "warmup"


# =========================
# Load Market Data
# =========================

DATA_FILE = DATA_DIR / "ohlcv_today.csv"
if not DATA_FILE.exists():
    raise FileNotFoundError(f"Missing data file: {DATA_FILE}")

df = pd.read_csv(DATA_FILE)
df["date"] = pd.to_datetime(df["date"])

# =========================
# Selector Config
# =========================

phase = infer_phase(df)

CFG = SelectorConfig(
    phase=phase
)

LARGECAPS = ["005930", "000660"]

# =========================
# Theme Score (stub)
# =========================

theme_score_map = {}

# =========================
# Run Selector
# =========================

result = select_watchlist(
    df,
    cfg=CFG,
    largecap_symbols=LARGECAPS,
    theme_score_map=theme_score_map,
)

# =========================
# Save Result
# =========================

today = datetime.now().strftime("%Y%m%d")
output = {
    "date": today,
    "phase": phase,
    "largecap": result["largecap"],
    "volume": result["volume"],
    "structure": result["structure"],
    "theme": result["theme"],
}

out_file = OUTPUT_DIR / f"watchlist_{today}.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("✅ Watchlist generated")
print(json.dumps(output, ensure_ascii=False, indent=2))
print(f"📁 Saved to: {out_file}")
