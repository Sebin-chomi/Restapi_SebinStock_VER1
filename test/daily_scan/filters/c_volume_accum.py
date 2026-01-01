# daily_scan/filters/c_volume_accum.py
"""
C_volume_accum
--------------
1차 필터링용 '거래량 누적 증가' 후보 생성기 (실전 기준)

역할:
- 이벤트성 폭발(A), 변동성 점프(B)가 없을 때
  조용한 수급 변화를 포착
- 신호가 없으면 0을 반환하는 것이 정상 동작

출력:
- daily_scan/inputs/C_volume_accum.csv
- CSV 형식: symbol 단일 컬럼
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

import pandas as pd


# ======================================================
# 🔧 설정 (실전 기준)
# ======================================================
@dataclass(frozen=True)
class VolumeAccumConfig:
    lookback_days: int = 20  # 과거 기준 구간
    recent_days: int = 5  # 최근 누적 구간
    accum_ratio: float = 1.3  # 최근 거래량 30% 증가

    # 유동성 선필터 (실전 최소 기준)
    min_avg_value_krw: int = 500_000_000  # 5억

    markets: tuple[str, ...] = ("KOSPI", "KOSDAQ")


# ======================================================
# 유틸
# ======================================================
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


# ======================================================
# 데이터 수집 (pykrx)
# ======================================================
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


# ======================================================
# 메인 로직
# ======================================================
def generate_c_volume_accum(
    asof: Optional[dt.date] = None,
    cfg: VolumeAccumConfig = VolumeAccumConfig(),
    out_path: Optional[Path] = None,
    verbose: bool = True,
) -> Path:
    asof = asof or _today()

    end = asof.strftime("%Y%m%d")
    start_date = asof - dt.timedelta(days=max(90, cfg.lookback_days * 4))
    start = start_date.strftime("%Y%m%d")

    inputs_dir = _inputs_dir()
    out_path = out_path or (inputs_dir / "C_volume_accum.csv")

    if verbose:
        print(f"[C_VOL_ACCUM] asof={asof}")
        print(f"[C_VOL_ACCUM] period={start} ~ {end}")
        print(f"[C_VOL_ACCUM] config={cfg}")
        print(f"[C_VOL_ACCUM] output={out_path}")

    symbols = _get_universe_pykrx(end, cfg.markets)
    if verbose:
        print(f"[C_VOL_ACCUM] universe size={len(symbols)}")

    picked: List[str] = []

    for idx, sym in enumerate(symbols, start=1):
        df = _get_ohlcv_pykrx(sym, start, end)
        if df.empty or "거래량" not in df.columns or "거래대금" not in df.columns:
            continue

        vol = df["거래량"].dropna()
        val = df["거래대금"].dropna()

        if len(vol) < (cfg.lookback_days + cfg.recent_days):
            continue

        # ===== 유동성 선필터 =====
        avg_val = float(val.iloc[-cfg.lookback_days :].mean())
        if avg_val < cfg.min_avg_value_krw:
            continue

        # ===== 거래량 누적 비교 =====
        recent_avg = float(vol.iloc[-cfg.recent_days :].mean())
        past_avg = float(vol.iloc[-(cfg.lookback_days + cfg.recent_days) : -cfg.recent_days].mean())

        if past_avg <= 0:
            continue

        if (recent_avg / past_avg) >= cfg.accum_ratio:
            picked.append(sym)

        if verbose and idx % 300 == 0:
            print(f"[C_VOL_ACCUM] processed={idx}/{len(symbols)} " f"picked={len(picked)}")

    _write_symbol_csv(picked, out_path)

    if verbose:
        print(f"[C_VOL_ACCUM] DONE picked={len(picked)}")

    return out_path


# ======================================================
# 단독 실행
# ======================================================
if __name__ == "__main__":
    generate_c_volume_accum(verbose=True)
