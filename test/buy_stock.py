# buy_stock.py
import requests
import json

from config import host_url, FAKE_MODE
from login import fn_au10001 as get_token
from holding import add_holding


# ==================================================
# 📥 주식 매수 주문
# ==================================================
def fn_kt10000(stk_cd, ord_qty, ord_uv, cont_yn='N', next_key='', token=None):

    # ===============================
    # 🧪 TEST MODE (가짜 매수)
    # ===============================
    if FAKE_MODE:
        qty = int(ord_qty)
        price = int(ord_uv)

        print(f"🧪 [FAKE BUY] {stk_cd} {qty}주 @ {price}")
        add_holding(stk_cd, qty, price)

        return {
            "success": True,
            "mode": "FAKE",
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
        'api-id': 'kt10000',
    }

    params = {
        'dmst_stex_tp': 'KRX',
        'stk_cd': stk_cd,
        'ord_qty': f'{ord_qty}',
        'ord_uv': f'{ord_uv}',
        'trde_tp': '0',
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
        print(f"❌ 매수 주문 오류: {e}")
        return {
            "success": False,
            "error": str(e),
        }
