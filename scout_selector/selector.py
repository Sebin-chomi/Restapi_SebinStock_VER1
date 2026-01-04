# selector.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import math
import pandas as pd

# =========================
# Config
# =========================

@dataclass(frozen=True)
class SelectionQuota:
    volume: int = 2
    structure: int = 2
    theme: int = 2
    largecap: int = 2


@dataclass(frozen=True)
class SelectorConfig:
    phase: str = "warmup"  # "warmup" | "normal"
    quota: SelectionQuota = SelectionQuota()

    min_price: float = 500.0
    min_turnover_krw: float = 2e9
    min_avg_vol_20: float = 50_000

    vol_spike_ratio_min: float = 2.0
    intraday_volatility_min: float = 0.03

    struct_trend_days: int = 5
    struct_range_min: float = 0.02
    struct_range_max: float = 0.10

    theme_min_score: float = 0.4

    w_turnover: float = 0.35
    w_vol_spike: float = 0.35
    w_volatility: float = 0.30

    w_trend: float = 0.45
    w_cleanliness: float = 0.30
    w_reasonable_range: float = 0.25

    w_theme: float = 0.70
    w_theme_turnover: float = 0.30


# =========================
# Helpers
# =========================

def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _z_norm(series: pd.Series) -> pd.Series:
    std = series.std(ddof=0)
    if std == 0 or math.isnan(std):
        return pd.Series(0.0, index=series.index)
    return (series - series.mean()) / std


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


# =========================
# Features
# =========================

def compute_features(df: pd.DataFrame, cfg: SelectorConfig, lookback: int = 20) -> pd.DataFrame:
    df = df.sort_values(["symbol", "date"]).copy()

    df["vol_avg"] = df.groupby("symbol")["volume"].transform(
        lambda s: s.rolling(lookback, min_periods=1).mean()
    )

    df["hlc_volatility"] = (df["high"] - df["low"]) / df["close"].replace(0, pd.NA)

    df["vol_spike_ratio"] = (
        df["volume"] / df["vol_avg"].replace(0, pd.NA)
    ).fillna(1.0)

    N = cfg.struct_trend_days
    df["trend"] = df.groupby("symbol")["close"].transform(
        lambda s: s.pct_change(N).fillna(0.0)
    )

    df["ma5"] = df.groupby("symbol")["close"].transform(
        lambda s: s.rolling(5, min_periods=1).mean()
    )
    df["above_ma5"] = (df["close"] > df["ma5"]).astype(int)
    df["clean"] = df.groupby("symbol")["above_ma5"].transform(
        lambda s: s.rolling(5, min_periods=1).mean().fillna(0.5)
    )

    return df


# =========================
# Scoring
# =========================

def score_volume(latest: pd.DataFrame, cfg: SelectorConfig) -> pd.Series:
    z_turn = _z_norm(latest["turnover_krw"].fillna(0)).map(_sigmoid)
    z_spike = _z_norm(latest["vol_spike_ratio"]).map(_sigmoid)
    z_vola = _z_norm(latest["hlc_volatility"].fillna(0)).map(_sigmoid)

    score = (
        cfg.w_turnover * z_turn +
        cfg.w_vol_spike * z_spike +
        cfg.w_volatility * z_vola
    )

    if cfg.phase == "normal":
        ok = (
            (latest["vol_spike_ratio"] >= cfg.vol_spike_ratio_min) &
            (latest["hlc_volatility"] >= cfg.intraday_volatility_min)
        )
        return score.where(ok, 0.0)

    return score


def score_structure(latest: pd.DataFrame, cfg: SelectorConfig) -> pd.Series:
    trend_score = latest["trend"].abs().apply(lambda x: _clamp(x / 0.10))
    clean_score = latest["clean"].apply(lambda x: _clamp(1 - abs(x - 0.6) / 0.6))
    vola = latest["hlc_volatility"].fillna(0)

    range_score = vola.apply(
        lambda x: 1.0 if cfg.struct_range_min <= x <= cfg.struct_range_max else 0.0
    )

    score = (
        cfg.w_trend * trend_score +
        cfg.w_cleanliness * clean_score +
        cfg.w_reasonable_range * range_score
    ).clip(0, 1)

    if cfg.phase == "normal":
        return score.where(
            (vola >= cfg.struct_range_min) & (vola <= cfg.struct_range_max),
            0.0
        )

    return score


def score_theme(latest: pd.DataFrame, theme_score: pd.Series, cfg: SelectorConfig) -> pd.Series:
    ts = theme_score.fillna(0).clip(0, 1)
    z_turn = _z_norm(latest["turnover_krw"].fillna(0)).map(_sigmoid)

    score = (cfg.w_theme * ts + cfg.w_theme_turnover * z_turn).clip(0, 1)

    if cfg.phase == "normal":
        return score.where(ts >= cfg.theme_min_score, 0.0)

    return score


# =========================
# Selection
# =========================

def select_watchlist(
    df: pd.DataFrame,
    *,
    cfg: SelectorConfig,
    largecap_symbols: List[str],
    theme_score_map: Optional[Dict[str, float]] = None,
) -> Dict[str, List[Tuple[str, float]]]:

    df_feat = compute_features(df, cfg)
    latest = df_feat.groupby("symbol", as_index=False).tail(1).set_index("symbol")

    if cfg.phase == "normal":
        universe = latest[
            (latest["close"] >= cfg.min_price) &
            (latest["turnover_krw"] >= cfg.min_turnover_krw) &
            (latest["vol_avg"] >= cfg.min_avg_vol_20)
        ]
    else:
        universe = latest[latest["close"] >= cfg.min_price]

    largecap = [(s, 1.0) for s in largecap_symbols if s in latest.index]
    picked = {s for s, _ in largecap}

    vol_scores = score_volume(universe, cfg)
    struct_scores = score_structure(universe, cfg)

    theme_score_map = theme_score_map or {}
    theme_series = pd.Series(
        {s: theme_score_map.get(s, 0.0) for s in universe.index}
    )
    theme_scores = score_theme(universe, theme_series, cfg)

    def _pick(scores: pd.Series, k: int):
        out = []
        for sym, sc in scores.sort_values(ascending=False).items():
            if sym in picked or sc <= 0:
                continue
            out.append((sym, float(sc)))
            picked.add(sym)
            if len(out) >= k:
                break
        return out

    return {
        "largecap": largecap,
        "volume": _pick(vol_scores, cfg.quota.volume),
        "structure": _pick(struct_scores, cfg.quota.structure),
        "theme": _pick(theme_scores, cfg.quota.theme),
    }
