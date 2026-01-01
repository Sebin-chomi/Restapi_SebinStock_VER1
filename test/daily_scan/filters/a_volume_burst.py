# daily_scan/filters/a_volume_burst.py
"""
A_volume_burst
--------------
1차 필터링용 '거래량 폭증' 후보 생성기 (최적화 버전)

- 대상: 전 종목 (KOSPI + KOSDAQ)
- 목적:
    오늘 거래량이 최근 N일 평균 대비 급증했고,
    기본적인 거래대금 유동성을 만족하는 종목을 거칠게 추림
- 출력:
    daily_scan/inputs/A_volume_burst.csv
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
class VolumeBurstConfig:
    lookback_days: int = 20  # 몇 일전 데이터까지 가져올거니?
    burst_ratio: float = (
        2.0  # “오늘 거래량이 최근 평균보다 최소 2배 이상 많아야 통과” 1.2배는 평소변동
    )
    min_avg_volume: int = 50_000  #

    # ⭐ 최적화 핵심: 거래대금 선필터
    min_avg_value_krw: int = 1_500_000_000  # 평균 거래대금 15억

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
    unique = list(dict.fromkeys(symbols))  # 중복 제거 + 순서 유지
    df = pd.DataFrame({"symbol": unique})
    df.to_csv(path, index=False, encoding="utf-8")


# =========================
# 데이터 수집 (pykrx)
# =========================
def _get_universe_pykrx(date: str, markets: tuple[str, ...]) -> List[str]:
    try:
        from pykrx import stock
    except Exception as e:
        raise RuntimeError(
            "pykrx를 불러올 수 없습니다. " "`pip install pykrx` 후 다시 시도하세요."
        ) from e

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
def generate_a_volume_burst(
    asof: Optional[dt.date] = None,
    cfg: VolumeBurstConfig = VolumeBurstConfig(),
    out_path: Optional[Path] = None,
    verbose: bool = True,
) -> Path:
    asof = asof or _today()

    end = asof.strftime("%Y%m%d")
    start_date = asof - dt.timedelta(days=max(60, cfg.lookback_days * 3))
    start = start_date.strftime("%Y%m%d")

    inputs_dir = _inputs_dir()
    out_path = out_path or (inputs_dir / "A_volume_burst.csv")

    if verbose:
        print(f"[A_VOLUME_BURST] asof={asof}")
        print(f"[A_VOLUME_BURST] period={start} ~ {end}")
        print(f"[A_VOLUME_BURST] config={cfg}")
        print(f"[A_VOLUME_BURST] output={out_path}")

    symbols = _get_universe_pykrx(end, cfg.markets)
    if verbose:
        print(f"[A_VOLUME_BURST] universe size={len(symbols)}")

    picked: List[str] = []

    for idx, sym in enumerate(symbols, start=1):
        df = _get_ohlcv_pykrx(sym, start, end)
        if df.empty:
            continue

        # ======================
        # 1️⃣ 거래대금 선필터
        # ======================
        if "거래대금" not in df.columns:
            continue

        val = df["거래대금"].dropna()
        if len(val) < cfg.lookback_days + 1:
            continue

        avg_val = float(val.iloc[-(cfg.lookback_days + 1) : -1].mean())
        if avg_val < cfg.min_avg_value_krw:
            continue

        # ======================
        # 2️⃣ 거래량 폭증 체크
        # ======================
        if "거래량" not in df.columns:
            continue

        vol = df["거래량"].dropna()
        if len(vol) < cfg.lookback_days + 1:
            continue

        today_vol = float(vol.iloc[-1])
        avg_vol = float(vol.iloc[-(cfg.lookback_days + 1) : -1].mean())

        if avg_vol < cfg.min_avg_volume:
            continue

        if (today_vol / avg_vol) < cfg.burst_ratio:
            continue

        picked.append(sym)

        if verbose and idx % 300 == 0:
            print(f"[A_VOLUME_BURST] processed={idx}/{len(symbols)} " f"picked={len(picked)}")

    _write_symbol_csv(picked, out_path)

    if verbose:
        print(f"[A_VOLUME_BURST] DONE picked={len(picked)}")

    return out_path


# =========================
# 단독 실행
# =========================
if __name__ == "__main__":
    generate_a_volume_burst(verbose=True)
