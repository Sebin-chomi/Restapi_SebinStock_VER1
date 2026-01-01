# broker/sell_api.py
"""
매도 API 모듈

역할:
- 주식 매도 주문 실행
- 모의/실전 환경은 config에 위임
- 판단 로직 없음 (실행 전용)
"""

import requests
from typing import Dict

from config import (
    host_url,
    app_key,
    app_secret,
    ACCOUNT_NO,
    is_paper_trading,
)


# ==================================================
# 공통 헤더 생성
# ==================================================
def _make_headers(token: str, tr_id: str) -> Dict[str, str]:
    return {
        "Content-Type": "application/json",
        "authorization": f"Bearer {token}",
        "appKey": app_key,
        "appSecret": app_secret,
        "tr_id": tr_id,
    }


# ==================================================
# 시장가 매도
# ==================================================
def sell_market(token: str, symbol: str, qty: int) -> Dict:
    """
    시장가 매도

    return:
    {
        "success": bool,
        "msg": str,
        "raw": dict
    }
    """
    url = f"{host_url}/uapi/domestic-stock/v1/trading/order-cash"

    # 매도 TR ID
    tr_id = "VTTC0801U" if is_paper_trading else "TTTC0801U"

    headers = _make_headers(token, tr_id)

    body = {
        "CANO": ACCOUNT_NO[:8],
        "ACNT_PRDT_CD": ACCOUNT_NO[8:],
        "PDNO": symbol,
        "ORD_DVSN": "01",     # 01 = 시장가
        "ORD_QTY": str(qty),
        "ORD_UNPR": "0",
    }

    try:
        res = requests.post(url, headers=headers, json=body, timeout=5)
        res.raise_for_status()
        data = res.json()

        if data.get("rt_cd") != "0":
            return {
                "success": False,
                "msg": data.get("msg1", "sell failed"),
                "raw": data,
            }

        return {
            "success": True,
            "msg": "sell order accepted",
            "raw": data,
        }

    except Exception as e:
        return {
            "success": False,
            "msg": str(e),
            "raw": {},
        }
