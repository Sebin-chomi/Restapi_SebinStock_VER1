# check_n_buy.py
import time

from broker.balance_api import get_available_cash
from config import STRATEGY_MAX_CASH
from order_api import buy
from tel_logger import tel_log

_pending_orders = {}  # stk_cd -> 주문 진행 중 플래그
_balance_error_notified = False
_last_balance_error_ts = 0


def chk_n_buy(stk_cd: str, token: str, account_state):
    global _balance_error_notified, _last_balance_error_ts

    # ==================================================
    # 1. 이미 보유 중이면 매수 안 함
    # ==================================================
    if account_state.has_position(stk_cd):
        return

    # ==================================================
    # 2. 중복 주문 방지
    # ==================================================
    if _pending_orders.get(stk_cd):
        return

    # ==================================================
    # 3. 예수금 조회
    # ==================================================
    raw_cash = get_available_cash(token)

    # 🔴 핵심 수정: 조회 실패(None)와 0원 분리
    if raw_cash is None:
        now = time.time()

        # 예수금 조회 실패 알림은 최초 1회만
        if not _balance_error_notified:
            tel_log(
                title="BUY SKIPPED",
                body=f"- 종목: {stk_cd}\n- 사유: 예수금 조회 실패(API 오류)",
                stk_cd=stk_cd,
            )
            _balance_error_notified = True
            _last_balance_error_ts = now

        # 조회 실패 시에는 판단 보류 (루프만 유지)
        time.sleep(30)
        return

    # ==================================================
    # 4. 실제 예수금 0원인 경우
    # ==================================================
    if raw_cash <= 0:
        return

    # ==================================================
    # 5. 전략 상한 적용
    # ==================================================
    available_cash = min(raw_cash, STRATEGY_MAX_CASH)
    if available_cash <= 0:
        return

    # ==================================================
    # 6. 매수 시도
    # ==================================================
    buy_qty = 1
    _pending_orders[stk_cd] = True

    try:
        tel_log(
            title="BUY TRY",
            body=f"🟢 매수 시도\n- 종목: {stk_cd}\n- 수량: {buy_qty}주",
            stk_cd=stk_cd,
        )

        result = buy(stk_cd, buy_qty, token)

        if result.get("success"):
            account_state.refresh()
            tel_log(
                title="BUY SUCCESS",
                body="🔵 매수 체결 완료",
                stk_cd=stk_cd,
            )
        else:
            tel_log(
                title="BUY FAIL",
                body=f"❌ 매수 실패\n{result}",
                stk_cd=stk_cd,
            )

    finally:
        _pending_orders.pop(stk_cd, None)


def reset_daily_state():
    _pending_orders.clear()
