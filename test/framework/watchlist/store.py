# ===============================
# test/framework/watchlist/store.py
# ===============================

FIXED_WATCHLIST = ["005930", "000660", "035420"]  # 예시: 삼성전자, SK하이닉스, NAVER
_dynamic_watchlist: list[str] = []


def get_watchlist() -> list[str]:
    return FIXED_WATCHLIST + _dynamic_watchlist


def add_stock(stk_cd: str):
    if stk_cd not in _dynamic_watchlist and len(_dynamic_watchlist) < 3:
        _dynamic_watchlist.append(stk_cd)

def remove_stock(stk_cd: str):
    if stk_cd in _dynamic_watchlist:
        _dynamic_watchlist.remove(stk_cd)


def clear_dynamic():
    _dynamic_watchlist.clear()
