# daily_scan/filters/b_volatility_jump.py
"""
B_volatility_jump
-----------------
1차 필터링용 '변동성 점프' 후보 생성기

- 대상: 전 종목 (KOSPI + KOSDAQ)
- 기준:
    오늘 변동폭(고가-저가)/종가 가
    최근 N일 평균 변동폭 대비 K배 이상
- 출력:
    daily_scan/inputs/B_volatility_jump.csv
- CSV 형식:
    symbol 단일 컬럼
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

import pandas as pd


# =========================
# 설정
# =========================
@dataclass(frozen=True)
class VolatilityJumpConfig:
    lookback_days: int = 20
    jump_ratio: float = 1.4

    # 유동성 선필터 (속도 + 품질)
    min_avg_value_krw: int = 500_000_000  # 5억

    markets: tuple[str, ...] = ("KOSPI", "KOSDAQ")


# =========================
# 유틸
# =========================
def _today() -> dt.date:
    return dt.date.today()


def _inputs_dir() -> Path:
    base = Path(__file__).resolve().parents[1]  # daily_scan/
    inputs = base / "inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    return inputs


def _write_symbol_csv(symbols: Iterable[str], path: Path) -> None:
    unique = list(dict.fromkeys(symbols))
    pd.DataFrame({"symbol": unique}).to_csv(path, index=False, encoding="utf-8")


# =========================
# 데이터 수집 (pykrx)
# =========================
def _get_universe_pykrx(date: str, markets: tuple[str, ...]) -> List[str]:
    from pykrx import stock

    symbols: List[str] = []
    for m in markets:
        symbols.extend(stock.get_market_ticker_list(date, market=m))
    return list(dict.fromkeys(symbols))


def _get_ohlcv_pykrx(symbol: str, start: str, end: str) -> pd.DataFrame:
    from pykrx import stock

    df = stock.get_market_ohlcv_by_date(start, end, symbol)
    if df is None or df.empty:
        return pd.DataFrame()
    return df


# =========================
# 메인 로직
# =========================
def generate_b_volatility_jump(
    asof: Optional[dt.date] = None,
    cfg: VolatilityJumpConfig = VolatilityJumpConfig(),
    out_path: Optional[Path] = None,
    verbose: bool = True,
) -> Path:
    asof = asof or _today()

    end = asof.strftime("%Y%m%d")
    start_date = asof - dt.timedelta(days=max(60, cfg.lookback_days * 3))
    start = start_date.strftime("%Y%m%d")

    inputs_dir = _inputs_dir()
    out_path = out_path or (inputs_dir / "B_volatility_jump.csv")

    if verbose:
        print(f"[B_VOL_JUMP] asof={asof}")
        print(f"[B_VOL_JUMP] period={start} ~ {end}")
        print(f"[B_VOL_JUMP] config={cfg}")
        print(f"[B_VOL_JUMP] output={out_path}")

    symbols = _get_universe_pykrx(end, cfg.markets)
    if verbose:
        print(f"[B_VOL_JUMP] universe size={len(symbols)}")

    picked: List[str] = []

    for idx, sym in enumerate(symbols, start=1):
        df = _get_ohlcv_pykrx(sym, start, end)
        if df.empty:
            continue

        # ===== 유동성 선컷 =====
        if "거래대금" not in df.columns:
            continue
        val = df["거래대금"].dropna()
        if len(val) < cfg.lookback_days + 1:
            continue
        avg_val = float(val.iloc[-(cfg.lookback_days + 1) : -1].mean())
        if avg_val < cfg.min_avg_value_krw:
            continue

        # ===== 변동성 계산 =====
        need_cols = {"고가", "저가", "종가"}
        if not need_cols.issubset(df.columns):
            continue

        today = df.iloc[-1]
        today_range = (today["고가"] - today["저가"]) / max(today["종가"], 1)

        past = df.iloc[-(cfg.lookback_days + 1) : -1]
        past_range = ((past["고가"] - past["저가"]) / past["종가"]).mean()

        if past_range <= 0:
            continue

        if (today_range / past_range) >= cfg.jump_ratio:
            picked.append(sym)

        if verbose and idx % 300 == 0:
            print(f"[B_VOL_JUMP] processed={idx}/{len(symbols)} picked={len(picked)}")

    _write_symbol_csv(picked, out_path)

    if verbose:
        print(f"[B_VOL_JUMP] DONE picked={len(picked)}")

    return out_path


if __name__ == "__main__":
    generate_b_volatility_jump(verbose=True)
