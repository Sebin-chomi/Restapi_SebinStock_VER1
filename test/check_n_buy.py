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

    if not TEST_MODE and not is_trade_time():
        return

    if account_state.has_position(stk_cd):
        return

    if _pending_orders.get(stk_cd):
        return

    raw_cash = get_available_cash(token)
    if raw_cash is None or raw_cash <= 0:
        if not _balance_error_notified:
            tel_log(
                title="BUY SKIP",
                body="예수금 조회 실패",
                stk_cd=stk_cd,
            )
            _balance_error_notified = True
        return

    available_cash = min(raw_cash, STRATEGY_MAX_CASH)
    if available_cash <= 0:
        return

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
            tel_log(
                title="BUY FAIL",
                body=str(result),
                stk_cd=stk_cd,
            )

    finally:
        _pending_orders.pop(stk_cd, None)
