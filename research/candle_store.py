# candle_store.py

import random
from datetime import datetime, timedelta


# ======================================================
# 📊 최근 캔들 조회 (임시/테스트용)
# - 실전에서는 여기를 키움 REST 캔들 API로 교체
# ======================================================
def get_recent_candles(stk_cd: str, n: int = 200):
    """
    반환 형식:
    [
        {
            "time": "HHMM",
            "open": float,
            "high": float,
            "low": float,
            "close": float,
            "volume": int
        },
        ...
    ]
    """

    candles = []
    base_price = random.randint(50000, 80000)

    now = datetime.now()

    for i in range(n):
        t = now - timedelta(minutes=5 * (n - i))
        open_p = base_price + random.randint(-500, 500)
        close_p = open_p + random.randint(-300, 300)
        high_p = max(open_p, close_p) + random.randint(0, 200)
        low_p = min(open_p, close_p) - random.randint(0, 200)
        volume = random.randint(1000, 50000)

        candles.append({
            "time": t.strftime("%H%M"),
            "open": float(open_p),
            "high": float(high_p),
            "low": float(low_p),
            "close": float(close_p),
            "volume": int(volume),
        })

        base_price = close_p

    return candles


# ======================================================
# 📈 평균 거래량 계산
# ======================================================
def get_avg_volume(stk_cd: str, n: int = 200) -> float:
    candles = get_recent_candles(stk_cd, n)
    if not candles:
        return 0.0

    total = sum(c["volume"] for c in candles)
    return total / len(candles)
