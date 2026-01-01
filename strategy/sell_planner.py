from config import TEST_MODE


def should_sell(account_state, stk_cd, current_price):
    if TEST_MODE:
        return True

    pos = account_state.holdings.get(stk_cd)
    if not pos:
        return False

    return current_price >= pos["avg_price"] * 1.01


def sell_qty(account_state, stk_cd):
    if TEST_MODE:
        return 1

    pos = account_state.holdings.get(stk_cd)
    if not pos:
        return 0

    return pos["qty"]
