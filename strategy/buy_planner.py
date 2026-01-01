# strategy/buy_planner.py
"""
매수 판단 및 매수 금액 계산 모듈

역할:
- 오늘 신규 매수가 가능한지 판단
- 종목당 매수 금액 계산
- 주문 API 바로 직전 단계
"""

from account.account_state import AccountState


# ==================================================
# 전략 파라미터 (추후 config로 분리 가능)
# ==================================================
MAX_HOLDINGS = 5          # 최대 보유 종목 수
MIN_ORDER_CASH = 100_000 # 최소 주문 금액 (원)


# ==================================================
# 매수 가능 여부 판단
# ==================================================
def can_buy_today(account: AccountState) -> bool:
    """
    오늘 신규 매수가 가능한지 여부
    """
    if account.holding_count() >= MAX_HOLDINGS:
        return False

    if account.cash < MIN_ORDER_CASH:
        return False

    return True


def can_buy_symbol(account: AccountState, symbol: str) -> bool:
    """
    특정 종목을 오늘 살 수 있는지 여부
    """
    if account.has_position(symbol):
        return False

    return can_buy_today(account)


# ==================================================
# 매수 금액 계산
# ==================================================
def calc_buy_cash(account: AccountState) -> int:
    """
    종목당 매수 금액 계산
    (D+2 예수금 기준 균등 분할)
    """
    remain_slots = MAX_HOLDINGS - account.holding_count()
    if remain_slots <= 0:
        return 0

    cash_per_symbol = account.cash // remain_slots

    # 최소 주문 금액 미만이면 매수 안 함
    if cash_per_symbol < MIN_ORDER_CASH:
        return 0

    return cash_per_symbol
