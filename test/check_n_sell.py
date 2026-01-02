from common.utils import is_trade_time
from config import TEST_MODE
from test.order_api import sell
from test.price_api import get_current_price
from strategy.sell_planner import sell_qty
from test.tel_logger import tel_log


_pending_sell_orders = {}


def chk_n_sell(stk_cd: str, token: str, account_state):
    observer_result = {
        "triggered": False,
        "reason": None,
    }

    if not TEST_MODE and not is_trade_time():
        observer_result["reason"] = "NOT_TRADE_TIME"
        return observer_result

    if TEST_MODE:
        if stk_cd not in account_state.holdings:
            observer_result["reason"] = "NO_POSITION"
            return observer_result
    else:
        if not account_state.has_position(stk_cd):
            observer_result["reason"] = "NO_POSITION"
            return observer_result

    if _pending_sell_orders.get(stk_cd):
        observer_result["reason"] = "PENDING_ORDER"
        return observer_result

    try:
        current_price = get_current_price(stk_cd, token)
    except Exception:
        pos = account_state.holdings[stk_cd]
        current_price = int(pos["avg_price"] * 1.01)

        tel_log(
            title="TEST SELL PRICE",
            body=f"{current_price}",
            stk_cd=stk_cd,
        )

    qty = sell_qty(account_state, stk_cd)
    if qty <= 0:
        observer_result["reason"] = "SELL_QTY_ZERO"
        return observer_result

    _pending_sell_orders[stk_cd] = True

    try:
        tel_log(
            title="SELL TRY",
            body=f"{stk_cd} {qty}주",
            stk_cd=stk_cd,
        )

        result = sell(stk_cd, qty, token)

        if result.get("success"):
            observer_result["triggered"] = True
            observer_result["reason"] = "SELL_SUCCESS"

            if TEST_MODE:
                account_state.holdings.pop(stk_cd, None)

            tel_log(
                title="SELL SUCCESS",
                body="매도 완료",
                stk_cd=stk_cd,
            )
        else:
            observer_result["reason"] = "SELL_FAIL"

            tel_log(
                title="SELL FAIL",
                body=str(result),
                stk_cd=stk_cd,
            )

    finally:
        _pending_sell_orders.pop(stk_cd, None)

    return observer_result
