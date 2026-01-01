"""
Post-Market Daily Scan
- 실행 시점: 장 마감 후
- 목적: 다음날 관찰할 종목 후보 리스트 생성
- 주의: 매매 / 전략 / 주문 로직 없음
"""

import csv
from datetime import datetime
from pathlib import Path

from daily_scan.config import (
    SCAN_VERSION,
    WATCH_TIER_1,
    WATCH_TIER_2,
    MIN_TRADING_VALUE,
    VOLUME_AVG_PERIOD,
)

from daily_scan.inputs.kiwoom_conditions import load_condition_result
from daily_scan.data.ohlcv_loader import (
    load_daily_ohlcv,
    load_volume_history,
)

# =========================================================
# [ADD] 운영 안정용 제한값
# =========================================================
MAX_TIER1_COUNT = 30
MAX_TIER2_COUNT = 50


# =========================================================
# A. 거래량 점수
# =========================================================

def calc_volume_score(volume_ratio: float) -> int:
    if volume_ratio >= 2.5:
        return 25
    elif volume_ratio >= 1.5:
        return 16
    elif volume_ratio >= 1.0:
        return 8
    return 0


# =========================================================
# B. 캔들 구조 점수
# =========================================================

def calc_candle_score(open_, high, low, close) -> int:
    total_range = high - low
    if total_range <= 0:
        return 0

    body_ratio = abs(close - open_) / total_range
    if body_ratio < 0.2:
        body_score = 0
    elif body_ratio < 0.4:
        body_score = 8
    elif body_ratio < 0.7:
        body_score = 15
    else:
        body_score = 10

    upper = high - max(open_, close)
    lower = min(open_, close) - low
    wick_ratio = (upper + lower) / total_range
    if wick_ratio >= 0.7:
        wick_score = 0
    elif wick_ratio >= 0.5:
        wick_score = 5
    else:
        wick_score = 10

    return body_score + wick_score


# =========================================================
# C. 변동성 점수 (고저폭 %)
# =========================================================

def calc_volatility_score(high, low, close) -> int:
    if close <= 0:
        return 0

    range_pct = (high - low) / close * 100
    if range_pct < 1.5:
        return 5
    elif range_pct < 4.5:
        return 20
    elif range_pct < 7.0:
        return 10
    else:
        return 0


# =========================================================
# D. 유동성 점수
# =========================================================

def calc_liquidity_score(trading_value: int, close: int) -> int:
    if trading_value < 30_000_000_000:
        value_score = 0
    elif trading_value < 100_000_000_000:
        value_score = 8
    else:
        value_score = 15

    if close < 1_000:
        price_score = 0
    elif close < 5_000:
        price_score = 3
    else:
        price_score = 5

    return value_score + price_score


# =========================================================
# 메인 스캔
# =========================================================

def run_daily_scan(scan_date: str) -> list[dict]:
    print(f"\n[SCAN START] date={scan_date}, version={SCAN_VERSION}")

    symbols = set()
    source_map = {}

    for tag in ["A_volume_burst", "B_volatility_jump", "C_volume_accum"]:
        for symbol in load_condition_result(tag):
            symbols.add(symbol)
            source_map.setdefault(symbol, []).append(tag)

    print(f"[INFO] Total candidate symbols: {len(symbols)}")

    records = []

    for symbol in symbols:
        try:
            ohlcv = load_daily_ohlcv(symbol, scan_date)
            volume_hist = load_volume_history(symbol, VOLUME_AVG_PERIOD)
        except Exception as e:
            print(f"[SKIP] {symbol}: {e}")
            continue

        if not volume_hist:
            continue
        if ohlcv["trading_value"] < MIN_TRADING_VALUE:
            continue

        volume_avg = sum(volume_hist) / len(volume_hist)
        volume_ratio = ohlcv["volume"] / volume_avg if volume_avg > 0 else 0

        score_volume = calc_volume_score(volume_ratio)
        score_candle = calc_candle_score(
            ohlcv["open"], ohlcv["high"], ohlcv["low"], ohlcv["close"]
        )
        score_volatility = calc_volatility_score(
            ohlcv["high"], ohlcv["low"], ohlcv["close"]
        )
        score_liquidity = calc_liquidity_score(
            ohlcv["trading_value"], ohlcv["close"]
        )

        total_score = (
            score_volume
            + score_candle
            + score_volatility
            + score_liquidity
        )

        # [ADD] Tier 결정 이유 명확화
        if total_score >= WATCH_TIER_1:
            watch_tier = "TIER1"
            tier_reason = "TOTAL_SCORE_HIGH"
        elif total_score >= WATCH_TIER_2:
            watch_tier = "TIER2"
            tier_reason = "TOTAL_SCORE_MID"
        else:
            watch_tier = "NONE"
            tier_reason = "SCORE_LOW"

        records.append({
            "date": scan_date,
            "symbol": symbol,
            "source_tags": "|".join(source_map.get(symbol, [])),
            "volume_ratio": round(volume_ratio, 2),
            "score_volume": score_volume,
            "score_candle": score_candle,
            "score_volatility": score_volatility,
            "score_liquidity": score_liquidity,
            "score_total": total_score,
            "watch_tier": watch_tier,
            "tier_reason": tier_reason,          # [ADD]
            "scan_version": SCAN_VERSION,
        })

    print(f"[RESULT] scanned={len(records)}")

    # =====================================================
    # [ADD] Tier별 개수 제한 (운영 안정)
    # =====================================================
    tier1 = [r for r in records if r["watch_tier"] == "TIER1"][:MAX_TIER1_COUNT]
    tier2 = [r for r in records if r["watch_tier"] == "TIER2"][:MAX_TIER2_COUNT]

    return tier1 + tier2


# =========================================================
# CSV 저장 (FIXED)
# =========================================================

def save_scan_result_csv(records: list[dict], scan_date: str):
    # 🔥 프로젝트 루트 기준
    PROJECT_ROOT = Path(__file__).resolve().parents[1]

    output_dir = PROJECT_ROOT / "daily_scan" / "output"
    output_dir.mkdir(exist_ok=True, parents=True)

    if not records:
        print("[WARN] No records to save.")
        return

    file_path = output_dir / f"scan_result_{scan_date}.csv"

    with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)

    print(f"[SAVE] Scan result saved: {file_path}")


# =========================================================
# 실행 엔트리
# =========================================================

if __name__ == "__main__":
    today = datetime.now().strftime("%Y-%m-%d")
    results = run_daily_scan(today)
    save_scan_result_csv(results, today)
