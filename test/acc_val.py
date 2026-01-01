import requests
import pandas as pd
from config import host_url
from login import fn_au10001 as get_token

# 계좌평가현황요청
def fn_kt00004(print_df=False, cont_yn='N', next_key='', token=None):
    # 1. 요청할 API URL
    endpoint = '/api/dostk/acnt'
    url = host_url + endpoint

    # 토큰이 없는 경우 새로 발급
    if token is None:
        token = get_token()

    # 2. header 데이터
    headers = {
        'Content-Type': 'application/json;charset=UTF-8', # 컨텐츠타입
        'authorization': f'Bearer {token}', # 접근토큰
        'cont-yn': cont_yn, # 연속조회여부
        'next-key': next_key, # 연속조회키
        'api-id': 'kt00004', # TR명
    }

    # 3. 요청 데이터
    params = {
        'qry_tp': '0', # 상장폐지조회구분 0:전체, 1:상장폐지종목제외
        'dmst_stex_tp': 'KRX', # 국내거래소구분 KRX:한국거래소,NXT:넥스트트레이드
    }

    try:
        # 4. http POST 요청
        response = requests.post(url, headers=headers, json=params)
        res_data = response.json()

        # [수정포인트] 키가 없어도 에러가 나지 않도록 .get() 사용
        # 데이터가 없거나 점검 중일 때 에러 대신 빈 리스트를 반환합니다.
        stk_acnt_evlt_prst = res_data.get('stk_acnt_evlt_prst', [])

        if not stk_acnt_evlt_prst:
            # 텔레그램 명령 'R' 등에 대응하기 위해 로그 출력
            # print("보유 종목 데이터가 없습니다.") 
            return []

        # 데이터프레임 변환 및 출력 (필요 시)
        if print_df:
            df = pd.DataFrame(stk_acnt_evlt_prst)
            print(df)

        return stk_acnt_evlt_prst

    except Exception as e:
        print(f"acc_val.py 실행 중 오류 발생: {e}")
        return []

# 테스트용 코드
if __name__ == "__main__":
    import json
    test_token = get_token()
    result = fn_kt00004(print_df=True, token=test_token)
    print(json.dumps(result, indent=4, ensure_ascii=False))