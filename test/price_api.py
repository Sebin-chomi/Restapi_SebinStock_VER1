""" import requests
from config import app_key, app_secret, host_url, price_tr_id


def get_current_price(stk_cd, token):
    url = f"{host_url}/uapi/domestic-stock/v1/quotations/inquire-price"

    headers = {
        "authorization": f"Bearer {token}",
        "appkey": app_key,
        "appsecret": app_secret,
        "tr_id": price_tr_id,   # ⚠️ 키움 REST 기준 TR_ID
        "custtype": "P"
    }

    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": stk_cd
    }

    r = requests.get(url, headers=headers, params=params, timeout=5)
    r.raise_for_status()

    data = r.json()
    return int(data["output"]["stck_prpr"])
 """

import random


def get_current_price(stk_cd, token):
    """
    mock 환경용 임시 현재가
    실전 전환 시 이 함수만 교체
    """
    return random.randint(70000, 75000)
