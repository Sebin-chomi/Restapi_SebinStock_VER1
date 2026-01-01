# broker/order_api.py
"""
주문 API 모듈

역할:
- 주식 매수/매도 주문 실행
- 모의/실전 환경은 config에 위임
- 주문 결과만 반환 (판단 로직 없음)
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
# 매수 주문 (시장가, 1주)
# ==================================================
def buy_market(token: str, symbol: str, qty: int = 1) -> Dict:
    """
    시장가 매수

    return:
    {
        "success": bool,
        "msg": str,
        "raw": dict
    }
    """
    url = f"{host_url}/uapi/domestic-stock/v1/trading/order-cash"

    tr_id = "VTTC0802U" if is_paper_trading else "TTTC0802U"

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

        rt_cd = data.get("rt_cd")
        if rt_cd != "0":
            return {
                "success": False,
                "msg": data.get("msg1", "order failed"),
                "raw": data,
            }

        return {
            "success": True,
            "msg": "order accepted",
            "raw": data,
        }

    except Exception as e:
        return {
            "success": False,
            "msg": str(e),
            "raw": {},
        }
