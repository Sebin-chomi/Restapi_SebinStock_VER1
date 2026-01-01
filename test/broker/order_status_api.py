# broker/order_status_api.py
"""
주문 체결 / 미체결 조회 API

역할:
- 특정 계좌의 주문 체결 상태 조회
- 체결 / 미체결 / 부분체결 구분
- 판단 로직 없음 (조회 전용)
"""

import requests
from typing import List, Dict

from config import (
    host_url,
    app_key,
    app_secret,
    ACCOUNT_NO,
    is_paper_trading,
)


def get_order_status(token: str) -> List[Dict]:
    """
    주문 체결 상태 조회

    return 예시:
    [
        {
            "symbol": "005930",
            "order_no": "0001234567",
            "order_qty": 10,
            "filled_qty": 5,
            "unfilled_qty": 5,
            "status": "PARTIAL"
        }
    ]
    """
    url = f"{host_url}/uapi/domestic-stock/v1/trading/inquire-psbl-order"

    headers = {
        "authorization": f"Bearer {token}",
        "appKey": app_key,
        "appSecret": app_secret,
        "tr_id": "VTTC8036R" if is_paper_trading else "TTTC8036R",
    }

    params = {
        "CANO": ACCOUNT_NO[:8],
        "ACNT_PRDT_CD": ACCOUNT_NO[8:],
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": "",
    }

    try:
        res = requests.get(url, headers=headers, params=params, timeout=5)
        res.raise_for_status()
        data = res.json()

        results = []

        for item in data.get("output", []):
            order_qty = int(item.get("ord_qty", 0))
            filled_qty = int(item.get("exec_qty", 0))
            unfilled_qty = order_qty - filled_qty

            if filled_qty == 0:
                status = "OPEN"
            elif unfilled_qty == 0:
                status = "FILLED"
            else:
                status = "PARTIAL"

            results.append({
                "symbol": item.get("pdno"),
                "order_no": item.get("odno"),
                "order_qty": order_qty,
                "filled_qty": filled_qty,
                "unfilled_qty": unfilled_qty,
                "status": status,
            })

        return results

    except Exception as e:
        print(f"[order_status_api] failed: {e}")
        return []
