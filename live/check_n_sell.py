# check_n_sell.py
"""
Phase 2 매도 로직

원칙:
- 타임아웃 없음
- 가격 기준으로만 청산
- +2% 익절 / -1% 손절
- TEST_MODE에서는 항상 활성
"""

from config import TEST_MODE
from order_api import sell
from price_api import get_current_price
from strategy.sell_planner import sell_qty, should_sell
from tel_logger import tel_log

# 중복 매도 주문 방지
_pending_sell_orders = {}  # stk_cd -> True


def chk_n_sell(stk_cd: str, token: str, account_state, force: bool = False):
    """
    stk_cd : 종목코드
    token  : access token
    account_state : AccountState
    force  : Phase 2에서는 should_sell 결과에 따라 True로 호출
    """

    # ---------------------------------------------
    # 1️⃣ 보유 여부 확인
    # ---------------------------------------------
    if not account_state.has_position(stk_cd):
        return

    # ---------------------------------------------
    # 2️⃣ 중복 주문 방지
    # ---------------------------------------------
    if _pending_sell_orders.get(stk_cd):
        return

    # ---------------------------------------------
    # 3️⃣ 현재가 조회
    # ---------------------------------------------
    try:
        current_price = get_current_price(stk_cd, token)
    except Exception as e:
        tel_log(
            title="SELL SKIP",
            body=f"- 종목: {stk_cd}\n- 사유: 현재가 조회 실패\n{e}",
            stk_cd=stk_cd,
        )
        return

    # ---------------------------------------------
    # 4️⃣ 매도 판단 (+2% / -1%)
    # ---------------------------------------------
    if not should_sell(account_state, stk_cd, current_price):
        return

    qty = sell_qty(account_state, stk_cd)
    if qty <= 0:
        return

    # ---------------------------------------------
    # 5️⃣ 매도 실행
    # ---------------------------------------------
    _pending_sell_orders[stk_cd] = True

    try:
        tel_log(
            title="SELL TRY",
            body=(
                f"🔴 매도 시도\n"
                f"- 종목: {stk_cd}\n"
                f"- 현재가: {current_price}\n"
                f"- 수량: {qty}주"
            ),
            stk_cd=stk_cd,
        )

        result = sell(
            stk_cd,
            qty,
            token,
        )

        if result.get("success"):
            account_state.refresh()
            tel_log(
                title="SELL SUCCESS",
                body="✅ 매도 체결 완료",
                stk_cd=stk_cd,
            )
        else:
            tel_log(
                title="SELL FAIL",
                body=f"❌ 매도 실패\n{result}",
                stk_cd=stk_cd,
            )

    finally:
        _pending_sell_orders.pop(stk_cd, None)


def reset_daily_state():
    """일일 상태 초기화"""
    _pending_sell_orders.clear()
