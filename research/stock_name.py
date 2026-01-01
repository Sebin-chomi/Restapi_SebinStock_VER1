# stock_name.py
import requests
from config import host_url, app_key, app_secret

_name_cache = {}

def get_stock_name(stk_cd: str, token: str | None = None) -> str:
    """
    종목코드를 종목명으로 변환 (캐시 사용)
    """
    if stk_cd in _name_cache:
        return _name_cache[stk_cd]

    try:
        url = f"{host_url}/uapi/domestic-stock/v1/quotations/inquire-price"
        headers = {
            "authorization": f"Bearer {token}",
            "appkey": app_key,
            "appsecret": app_secret,
            "tr_id": "FHKST01010100",
        }
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": stk_cd,
        }

        res = requests.get(url, headers=headers, params=params, timeout=5)
        res.raise_for_status()

        name = res.json()["output"]["hts_kor_isnm"]
        _name_cache[stk_cd] = name
        return name

    except Exception:
        return stk_cd  # 실패 시 코드 그대로
