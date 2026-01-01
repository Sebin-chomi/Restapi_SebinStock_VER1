# sell_stock.py
import requests
import json

from config import host_url, FAKE_MODE
from login import fn_au10001 as get_token
from holding import get_holding, remove_holding
from risk_state import add_trade_pnl


# ==================================================
# 📤 주식 매도 주문
# ==================================================
def fn_kt10001(stk_cd, ord_qty, cont_yn='N', next_key='', token=None):

    holding = get_holding(stk_cd)

    # ===============================
    # 🧪 TEST MODE (가짜 매도)
    # ===============================
    if FAKE_MODE:
        if not holding:
            print(f"🧪 [FAKE SELL] 보유 없음: {stk_cd}")
            return {
                "success": False,
                "reason": "NO_HOLDING",
            }

        buy_price = holding["buy_price"]
        qty = holding["qty"]

        # TEST에서는 손익 0 처리
        sell_price = buy_price
        pnl = (sell_price - buy_price) * qty

        print(f"🧪 [FAKE SELL] {stk_cd} {qty}주 @ {sell_price}")
        add_trade_pnl(pnl)
        remove_holding(stk_cd)

        return {
            "success": True,
            "mode": "FAKE",
            "pnl": pnl,
        }

    # ===============================
    # 🔴 REAL MODE (키움 API)
    # ===============================
    if token is None:
        token = get_token()

    endpoint = '/api/dostk/ordr'
    url = host_url + endpoint

    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': cont_yn,
        'next-key': next_key,
        'api-id': 'kt10001',
    }

    params = {
        'dmst_stex_tp': 'KRX',
        'stk_cd': stk_cd,
        'ord_qty': ord_qty,
        'ord_uv': '',
        'trde_tp': '3',
        'cond_uv': '',
    }

    try:
        response = requests.post(url, headers=headers, json=params)
        res_json = response.json()

        return {
            "success": res_json.get("return_code") == "0",
            "raw": res_json,
        }

    except Exception as e:
        print(f"❌ 매도 주문 오류: {e}")
        return {
            "success": False,
            "error": str(e),
        }
