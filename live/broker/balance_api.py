"""
예수금(매수 가능 금액) 조회 모듈

역할:
- 실전: 증권사 API로 예수금 조회
- 테스트: config에 정의된 가짜 예수금 반환
- 판단 로직 없음 (조회 전용)
"""

import time

import requests

from config import (
    PAPER_CASH,
    account_no,
    account_product,
    app_key,
    app_secret,
    host_url,
    is_paper_trading,
)

# ======================================================
# 내부 캐시 (실전 API 호출 최소화)
# ======================================================
_last_fetch_ts = 0
_cached_cash = None

CACHE_SEC = 10


def get_available_cash(token: str):
    """
    현재 매수 가능한 예수금 반환 (원 단위)

    반환:
    - int  : 예수금
    - None : 실전 API 실패
    """

    # ==================================================
    # ✅ 테스트 모드 → 가짜 예수금 즉시 반환
    # ==================================================
    if is_paper_trading:
        return PAPER_CASH

    # ==================================================
    # 실전 모드
    # ==================================================
    global _last_fetch_ts, _cached_cash
    now = time.time()

    if _cached_cash is not None and now - _last_fetch_ts < CACHE_SEC:
        return _cached_cash

    url = f"{host_url}/uapi/domestic-stock/v1/trading/inquire-balance"

    headers = {
        "authorization": f"Bearer {token}",
        "appKey": app_key,
        "appSecret": app_secret,
        "tr_id": "TTTC8434R",
    }

    params = {
        "CANO": account_no[:8],
        "ACNT_PRDT_CD": account_product,
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

        cash = int(data["output2"][0]["ord_psbl_cash"])

        _cached_cash = cash
        _last_fetch_ts = now

        return cash

    except Exception as e:
        print(f"[balance_api] fetch failed: {e}")
        return None
