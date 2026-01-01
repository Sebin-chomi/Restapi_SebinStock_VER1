import requests
import json
from config import host_url
from login import fn_au10001 as get_token

# 주식호가요청
def fn_ka10004(stk_cd, cont_yn='N', next_key='', token=None):
	# 1. 요청할 API URL
	endpoint = '/api/dostk/mrkcond'
	url =  host_url + endpoint

	# 2. header 데이터
	headers = {
		'Content-Type': 'application/json;charset=UTF-8', # 컨텐츠타입
		'authorization': f'Bearer {token}', # 접근토큰
		'cont-yn': cont_yn, # 연속조회여부
		'next-key': next_key, # 연속조회키
		'api-id': 'ka10004', # TR명
	}

	# 3. 요청 데이터
	params = {
		'stk_cd': stk_cd, # 종목코드 거래소별 종목코드 (KRX:039490,NXT:039490_NX,SOR:039490_AL)
	}

	# 4. http POST 요청
	response = requests.post(url, headers=headers, json=params)
	sel_fpr_bid_raw = response.json()['sel_fpr_bid']

	try:
		sel_fpr_bid = abs(float(sel_fpr_bid_raw))
	except (ValueError, TypeError):
		print("매도최우선호가를 숫자로 변환할 수 없습니다:", sel_fpr_bid_raw)
		sel_fpr_bid = 0

	print('매도최우선호가(절대값): ', sel_fpr_bid)

	return sel_fpr_bid

	# 5. 응답 상태 코드와 데이터 출력
	print('Code:', response.status_code)
	print('Header:', json.dumps({key: response.headers.get(key) for key in ['next-key', 'cont-yn', 'api-id']}, indent=4, ensure_ascii=False))
	print('Body:', json.dumps(response.json(), indent=4, ensure_ascii=False))  # JSON 응답을 파싱하여 출력

# 실행 구간
if __name__ == '__main__':
	fn_ka10004('005930', token=get_token())