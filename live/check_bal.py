import requests
import json
from config import host_url
# 토큰 발급 함수를 다시 추가합니다.
from login import fn_au10001 as get_token

# 예수금상세현황요청 (D+2 추정 금액 포함)
def fn_kt00001(cont_yn='N', next_key='', token=None):
    # 만약 매개변수로 전달된 토큰이 없다면 새로 발급받습니다.
    if token is None:
        token = get_token()

    endpoint = '/api/dostk/acnt'
    url = host_url + endpoint

    # qry_tp: 3 (추정조회) 설정으로 D+1, D+2 예수금 데이터를 가져옵니다.
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

        # D+2일 후 예상 순수 예수금 (매도대금 포함된 금액)
        # 키움 API 필드명: d2_prev_blue_amt
        d2_balance = int(res_json.get('d2_prev_blue_amt', 0))
        
        # 만약 해당 필드가 없거나 0인 경우, 일반 예수금(entr)을 대안으로 사용
        if d2_balance == 0:
            d2_balance = int(res_json.get('entr', 0))

        print(f'💰 자금 확인 완료 (D+2): {d2_balance:,}원')
        return d2_balance

    except Exception as e:
        print(f"예수금 조회 중 오류 발생: {e}")
        return 0