import time

from test.broker.balance_api import get_available_cash
from config import STRATEGY_MAX_CASH, TEST_MODE
from test.order_api import buy
from test.tel_logger import tel_log
from common.utils import is_trade_time


_pending_orders = {}
_balance_error_notified = False


def chk_n_buy(stk_cd: str, token: str, account_state):
    global _balance_error_notified

    # 🔽 observer 기본 결과
    observer_result = {
        "triggered": False,
        "reason": None,
    }

    if not TEST_MODE and not is_trade_time():
        observer_result["reason"] = "NOT_TRADE_TIME"
        return observer_result

    if account_state.has_position(stk_cd):
        observer_result["reason"] = "ALREADY_HOLDING"
        return observer_result

    if _pending_orders.get(stk_cd):
        observer_result["reason"] = "PENDING_ORDER"
        return observer_result

    raw_cash = get_available_cash(token)
    if raw_cash is None or raw_cash <= 0:
        if not _balance_error_notified:
            tel_log(
                title="BUY SKIP",
                body="예수금 조회 실패",
                stk_cd=stk_cd,
            )
            _balance_error_notified = True

        observer_result["reason"] = "NO_CASH"
        return observer_result

    available_cash = min(raw_cash, STRATEGY_MAX_CASH)
    if available_cash <= 0:
        observer_result["reason"] = "CASH_LIMIT"
        return observer_result

    _pending_orders[stk_cd] = True
    buy_qty = 1

    try:
        tel_log(
            title="BUY TRY",
            body=f"{stk_cd} {buy_qty}주",
            stk_cd=stk_cd,
        )

        result = buy(stk_cd, buy_qty, token)

        if result.get("success"):
            observer_result["triggered"] = True
            observer_result["reason"] = "BUY_SUCCESS"

            # 🔥 TEST: 가짜 포지션 주입
            if TEST_MODE:
                account_state.holdings[stk_cd] = {
                    "qty": buy_qty,
                    "avg_price": 70000,
                }

                tel_log(
                    title="TEST POSITION INJECTED",
                    body="가짜 포지션 생성",
                    stk_cd=stk_cd,
                )
            else:
                account_state.refresh()

            tel_log(
                title="BUY SUCCESS",
                body="매수 완료",
                stk_cd=stk_cd,
            )
        else:
            observer_result["reason"] = "BUY_FAIL"

            tel_log(
                title="BUY FAIL",
                body=str(result),
                stk_cd=stk_cd,
            )

    finally:
        _pending_orders.pop(stk_cd, None)

    return observer_result
