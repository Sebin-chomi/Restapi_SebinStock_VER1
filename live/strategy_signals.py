# strategy_signals.py
"""
5분봉 캔들 패턴 신호 판단 모듈 (순수 함수)
- side-effect 없음 (상태 변경/주문/시간필터 없음)
- 입력: candles(list[dict]), box_high/box_low, avg_volume
- 출력: bool 또는 신호 개수(int)
"""

from __future__ import annotations

from typing import Dict, List, Optional


Candle = Dict[str, float]  # open/high/low/close/volume (volume는 int여도 float로 처리)


def _get(c: Candle, key: str, default: float = 0.0) -> float:
    v = c.get(key, default)
    try:
        return float(v)
    except Exception:
        return float(default)


def _body_size(c: Candle) -> float:
    o = _get(c, "open")
    cl = _get(c, "close")
    return abs(cl - o)


def _upper_wick(c: Candle) -> float:
    h = _get(c, "high")
    o = _get(c, "open")
    cl = _get(c, "close")
    return max(0.0, h - max(o, cl))


def _is_bearish(c: Candle) -> bool:
    return _get(c, "close") < _get(c, "open")


def _is_bullish(c: Candle) -> bool:
    return _get(c, "close") > _get(c, "open")


# =========================================================
# 1) 윗꼬리가 긴 음봉
# =========================================================
def is_long_upper_wick_bearish(
    candle: Candle,
    box_low: float,
    avg_volume: float,
    wick_ratio: float = 1.5,
    min_body: float = 1e-9,
) -> bool:
    """
    조건(AND)
    - 음봉(close < open)
    - 윗꼬리 >= 몸통 * wick_ratio
    - 종가 >= box_low
    - 거래량 >= avg_volume
    """
    if candle is None:
        return False

    if not _is_bearish(candle):
        return False

    body = max(_body_size(candle), min_body)
    upper = _upper_wick(candle)

    if upper < body * wick_ratio:
        return False

    if _get(candle, "close") < float(box_low):
        return False

    if _get(candle, "volume") < float(avg_volume):
        return False

    return True


# =========================================================
# 2) 연속 3개의 양봉 (HL 구조 + 박스 상단 근처)
# =========================================================
def is_three_bullish(
    candles: List[Candle],
    box_high: float,
    avg_volume: float,
    near_box_pct: float = 0.01,
) -> bool:
    """
    최근 3봉을 사용.
    조건(AND)
    - 종가 3연속 상승: close[-1] > close[-2] > close[-3]
    - 저가 3연속 상승: low[-1] > low[-2] > low[-3]
    - (최근 3봉) 고가 최대치가 box_high * (1 + near_box_pct) 이하 (박스 상단 근처)
    - 최근 3봉 평균 거래량 >= avg_volume
    """
    if not candles or len(candles) < 3:
        return False

    c1, c2, c3 = candles[-3], candles[-2], candles[-1]

    # 3연속 양봉 자체를 강제하지는 않고(갭/미세음봉 등 노이즈),
    # 더 중요한 "종가/저가 상승 구조"를 핵심으로 둠.
    close1, close2, close3 = _get(c1, "close"), _get(c2, "close"), _get(c3, "close")
    low1, low2, low3 = _get(c1, "low"), _get(c2, "low"), _get(c3, "low")

    if not (close3 > close2 > close1):
        return False
    if not (low3 > low2 > low1):
        return False

    # 박스 상단 근처(너무 멀리 위로 가버리면 추격 가능성↑)
    max_high = max(_get(c1, "high"), _get(c2, "high"), _get(c3, "high"))
    if max_high > float(box_high) * (1.0 + near_box_pct):
        return False

    # 거래량 필터 (최근 3봉 평균)
    v_avg3 = (_get(c1, "volume") + _get(c2, "volume") + _get(c3, "volume")) / 3.0
    if v_avg3 < float(avg_volume):
        return False

    return True


# =========================================================
# 3) 하락장악형 (Bullish Engulfing)
# =========================================================
def is_bullish_engulfing(
    candles: List[Candle],
    box_low: float,
    avg_volume: float,
    volume_mult: float = 1.2,
) -> bool:
    """
    최근 2봉을 사용.
    조건(AND)
    - 이전 봉 음봉
    - 현재 봉 양봉
    - 현재 봉 몸통이 이전 봉 몸통을 완전히 포괄:
        curr.open <= prev.close AND curr.close >= prev.open
    - curr.volume >= avg_volume * volume_mult
    - curr.close >= box_low
    """
    if not candles or len(candles) < 2:
        return False

    prev, curr = candles[-2], candles[-1]

    if not _is_bearish(prev):
        return False
    if not _is_bullish(curr):
        return False

    prev_open, prev_close = _get(prev, "open"), _get(prev, "close")
    curr_open, curr_close = _get(curr, "open"), _get(curr, "close")

    # 장악형(몸통 포괄)
    if not (curr_open <= prev_close and curr_close >= prev_open):
        return False

    if _get(curr, "volume") < float(avg_volume) * float(volume_mult):
        return False

    if curr_close < float(box_low):
        return False

    return True


# =========================================================
# 신호 카운트(전략에서 쓰는 단일 인터페이스)
# =========================================================
def count_buy_signals(
    candles: List[Candle],
    box_high: float,
    box_low: float,
    avg_volume: float,
    wick_ratio: float = 1.5,
    near_box_pct: float = 0.01,
    engulf_vol_mult: float = 1.2,
) -> int:
    """
    3개 신호 중 True 개수(0~3)를 반환.
    - 윗꼬리 긴 음봉: 최근 1봉 기준
    - 3연속 양봉(HL): 최근 3봉 기준
    - 하락장악형: 최근 2봉 기준
    """
    if not candles:
        return 0

    cnt = 0
    last = candles[-1]

    if is_long_upper_wick_bearish(last, box_low=box_low, avg_volume=avg_volume, wick_ratio=wick_ratio):
        cnt += 1

    if is_three_bullish(candles, box_high=box_high, avg_volume=avg_volume, near_box_pct=near_box_pct):
        cnt += 1

    if is_bullish_engulfing(candles, box_low=box_low, avg_volume=avg_volume, volume_mult=engulf_vol_mult):
        cnt += 1

    return cnt


def explain_buy_signals(
    candles: List[Candle],
    box_high: float,
    box_low: float,
    avg_volume: float,
    wick_ratio: float = 1.5,
    near_box_pct: float = 0.01,
    engulf_vol_mult: float = 1.2,
) -> Dict[str, bool]:
    """
    디버깅/로그용: 각 신호별 True/False를 딕셔너리로 반환.
    (check_n_buy에서 실패원인 알림/로그 만들 때 유용)
    """
    if not candles:
        return {
            "wick_bear": False,
            "three_bull": False,
            "engulf": False,
        }

    last = candles[-1]
    return {
        "wick_bear": is_long_upper_wick_bearish(last, box_low=box_low, avg_volume=avg_volume, wick_ratio=wick_ratio),
        "three_bull": is_three_bullish(candles, box_high=box_high, avg_volume=avg_volume, near_box_pct=near_box_pct),
        "engulf": is_bullish_engulfing(candles, box_low=box_low, avg_volume=avg_volume, volume_mult=engulf_vol_mult),
    }
