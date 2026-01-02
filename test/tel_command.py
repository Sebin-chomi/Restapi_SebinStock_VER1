# 정찰봇 감시 종목 (동적 주입용)
_DYNAMIC_WATCHLIST = []


MAX_DYNAMIC = 6


def add_stock(stk_cd: str):
    if stk_cd in _DYNAMIC_WATCHLIST:
        return
    if len(_DYNAMIC_WATCHLIST) >= MAX_DYNAMIC:
        return
    _DYNAMIC_WATCHLIST.append(stk_cd)


def remove_stock(stk_cd: str):
    if stk_cd in _DYNAMIC_WATCHLIST:
        _DYNAMIC_WATCHLIST.remove(stk_cd)


def get_watchlist():
    return list(_DYNAMIC_WATCHLIST)


def clear_dynamic():
    _DYNAMIC_WATCHLIST.clear()
