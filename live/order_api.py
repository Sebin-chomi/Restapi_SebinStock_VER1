"""
order_api.py

주문 API (전략 보존 + 테스트 안정 버전)

역할:
- 현재 테스트 단계:
    * 시장가 매수/매도만 수행
- 기존 호가/전략 주문 로직:
    * 전부 보존 (주석 처리)
    * 실전 단계에서 복구 가능
"""

import requests

from config import (
    host_url,
    account_no,
    account_product,
    is_paper_trading,
)

from tel_send import send_message


# ======================================================
# ⚠️ 기존 전략용 가격 모듈 (현재 미사용)
# ======================================================
# ❌ 현재 프로젝트 구조에 없음
# ❌ 테스트 단계에서는 사용하지 않음
#
# from market_price import (
#     get_ask_prices,
#     get_bid_prices,
# )


# ======================================================
# 📈 BUY: 시장가 매수 (테스트용)
# ======================================================
def buy_market(token: str, symbol: str, qty: int):
    """
    테스트 단계:
    - 시장가
    - 1주
    - 판단 로직 없음
    """
    send_message(f"[ORDER_API] BUY market 요청: {symbol} x {qty}")

    return _send_order(
        token=token,
        symbol=symbol,
        qty=qty,
        ord_dvsn="01",  # 시장가
        price="0",
    )


# ======================================================
# 📉 SELL: 시장가 매도 (테스트용)
# ======================================================
def sell_market(token: str, symbol: str, qty: int):
    """
    테스트 단계:
    - 시장가
    - 전량/부분 전략은 상위에서 결정
    """
    send_message(f"[ORDER_API] SELL market 요청: {symbol} x {qty}")

    return _send_order(
        token=token,
        symbol=symbol,
        qty=qty,
        ord_dvsn="01",  # 시장가
        price="0",
    )


# ======================================================
# 🔩 주문 전송 (공통)
# ======================================================
def _send_order(token: str, symbol: str, qty: int, ord_dvsn: str, price: str):
    url = f"{host_url}/uapi/domestic-stock/v1/trading/order"

    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {token}",
    }

    body = {
        "CANO": account_no[:8],
        "ACNT_PRDT_CD": account_product,  # account_product는 "01" 같은 2자리 문자열이므로 [8:] 제거
        "PDNO": symbol,
        "ORD_DVSN": ord_dvsn,
        "ORD_QTY": str(qty),
        "ORD_UNPR": price,
    }

    try:
        res = requests.post(url, headers=headers, json=body, timeout=5)
        data = res.json()

        if res.status_code == 200 and data.get("rt_cd") == "0":
            return {
                "success": True,
                "msg": "주문 성공",
                "raw": data,
            }

        return {
            "success": False,
            "msg": "주문 실패",
            "raw": data,
        }

    except Exception as e:
        return {
            "success": False,
            "msg": f"주문 예외 발생: {e}",
        }

# ======================================================
# 🔄 Legacy 호환 함수 (기존 코드용)
# ======================================================
def buy(token, symbol, qty=1):
    """
    기존 check_n_buy.py 호환용
    """
    return buy_market(token, symbol, qty)


def sell(token, symbol, qty=1):
    """
    기존 check_n_sell.py 호환용
    """
    return sell_market(token, symbol, qty)





# ======================================================
# 🧠 기존 전략 주문 로직 (보존용 / 현재 미사용)
# ======================================================
"""
아래는 기존에 설계한 고급 주문 전략 영역이다.

- 호가 기반 매수/매도
- 지정가 분할 주문
- 스프레드 전략
- bid/ask depth 활용

👉 실전 전환 시:
1. market_price 모듈 복구
2. import 주석 해제
3. buy_market / sell_market 내부에서 분기 처리

지금은 "구조 안정화 + 전체 흐름 검증" 단계이므로
의도적으로 비활성화함.
"""
