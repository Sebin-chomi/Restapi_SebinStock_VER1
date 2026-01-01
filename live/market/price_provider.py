# market/price_provider.py
"""
현재가 조회 (REST 기반 가격 provider)

역할:
- 종목의 현재가를 증권사 API로 조회
- 판단 로직 없음
- 전략/매도 로직에 가격만 제공
"""

import time
import requests

from config import (
    host_url,
    app_key,
    app_secret,
    is_paper_trading,
)


# ==================================================
# 캐시 (과도한 호출 방지)
# ==================================================
_price_cache = {}
CACHE_SEC = 3  # 3초 캐시


def get_current_price(token: str, symbol: str) -> float:
    """
    종목 현재가 조회

    return:
        float: 현재가
    """
    now = time.time()

    # 캐시 사용
    if symbol in _price_cache:
        price, ts = _price_cache[symbol]
        if now - ts < CACHE_SEC:
            return price

    url = f"{host_url}/uapi/domestic-stock/v1/quotations/inquire-price"

    headers = {
        "authorization": f"Bearer {token}",
        "appKey": app_key,
        "appSecret": app_secret,
        "tr_id": "VTTC8001R" if is_paper_trading else "TTTC8001R",
    }

    params = {
        "FID_COND_MRKT_DIV_CODE": "J",  # 주식
        "FID_INPUT_ISCD": symbol,
    }

    try:
        res = requests.get(url, headers=headers, params=params, timeout=5)
        res.raise_for_status()
        data = res.json()

        price = float(data["output"]["stck_prpr"])

        _price_cache[symbol] = (price, now)
        return price

    except Exception as e:
        print(f"[price_provider] failed: {symbol} / {e}")
        return 0.0
