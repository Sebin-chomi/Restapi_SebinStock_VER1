# broker/holdings_api.py
"""
보유 종목 조회 모듈

역할:
- 현재 계좌에 보유 중인 종목 목록 조회
- 모의/실전 환경 판단은 config에 위임
- 계산/판단 로직 없음 (조회 전용)
"""

import time
import requests
from typing import Dict

from config import (
    host_url,
    app_key,
    app_secret,
    ACCOUNT_NO,
    is_paper_trading,
)

# =====================================================
# ⏱️ 캐시 설정 (API 호출 최소화)
# =====================================================
_last_fetch_ts = 0
_cached_holdings: Dict[str, dict] = {}

CACHE_SEC = 10  # 10초 캐시


# =====================================================
# 📦 보유 종목 조회
# =====================================================
def get_holdings(token: str) -> Dict[str, dict]:
    """
    현재 보유 종목 조회

    return:
    {
        "005930": {
            "qty": 10,
            "avg_price": 71200.0,
        },
        ...
    }
    """
    global _last_fetch_ts, _cached_holdings

    now = time.time()
    if now - _last_fetch_ts < CACHE_SEC:
        return _cached_holdings

    url = f"{host_url}/uapi/domestic-stock/v1/trading/inquire-balance"

    headers = {
        "authorization": f"Bearer {token}",
        "appKey": app_key,
        "appSecret": app_secret,
        # 모의 / 실전 TR ID 자동 선택
        "tr_id": "VTTC8434R" if is_paper_trading else "TTTC8434R",
    }

    params = {
        "CANO": ACCOUNT_NO[:8],
        "ACNT_PRDT_CD": ACCOUNT_NO[8:],
        "AFHR_FLPR_YN": "N",
        "OFL_YN": "",
        "INQR_DVSN": "02",
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "00",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": "",
    }

    try:
        res = requests.get(url, headers=headers, params=params, timeout=5)
        res.raise_for_status()
        data = res.json()

        holdings: Dict[str, dict] = {}

        # 🔹 output1 = 보유 종목 리스트
        for item in data.get("output1", []):
            # 종목코드 방어 (실전 필수)
            symbol = (
                item.get("pdno")
                or item.get("stk_cd")
                or item.get("symbol")
            )
            if not symbol:
                continue

            # 보유 수량
            qty = int(item.get("hldg_qty") or 0)
            if qty <= 0:
                continue

            # 평균단가
            avg_price = float(item.get("pchs_avg_pric") or 0)

            holdings[symbol] = {
                "qty": qty,
                "avg_price": avg_price,
            }

        _cached_holdings = holdings
        _last_fetch_ts = now
        return holdings

    except Exception as e:
        print(f"[holdings_api] fetch failed: {e}")
        return {}
