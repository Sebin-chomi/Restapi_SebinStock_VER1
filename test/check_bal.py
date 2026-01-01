# check_bal.py
import requests
import json

from config import host_url, FAKE_MODE, FAKE_CASH
from login import fn_au10001 as get_token


# ==================================================
# 💰 예수금 조회 (D+2 기준)
# - TEST(FAKE_MODE): 가짜 예수금 반환
# - REAL: 키움 API 조회
# ==================================================
def fn_kt00001(cont_yn='N', next_key='', token=None):
    # ===============================
    # 🧪 TEST MODE (가짜 예수금)
    # ===============================
    if FAKE_MODE:
        print(f"🧪 [FAKE BALANCE] 예수금 반환: {FAKE_CASH:,}원")
        return FAKE_CASH

    # ===============================
    # 🔴 REAL MODE (키움 API)
    # ===============================
    if token is None:
        token = get_token()

    endpoint = '/api/dostk/acnt'
    url = host_url + endpoint

    # qry_tp = 3 : D+1, D+2 추정 예수금 포함
    params = {
        'qry_tp': '3',
    }

    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': cont_yn,
        'next-key': next_key,
        'api-id': 'kt00001',
    }

    try:
        response = requests.post(url, headers=headers, json=params)
        res_json = response.json()

        # D+2 추정 예수금 (우선)
        d2_balance = int(res_json.get('d2_prev_blue_amt', 0))

        # fallback: 일반 예수금
        if d2_balance == 0:
            d2_balance = int(res_json.get('entr', 0))

        print(f"💰 자금 확인 완료 (D+2): {d2_balance:,}원")
        return d2_balance

    except Exception as e:
        print(f"❌ 예수금 조회 중 오류 발생: {e}")
        return 0
