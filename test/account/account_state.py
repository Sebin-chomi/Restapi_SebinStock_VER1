# account/account_state.py

from test.broker.balance_api import get_available_cash
from config import STRATEGY_MAX_CASH, TEST_MODE


class AccountState:
    def __init__(self, token: str):
        self.token = token
        self.cash = 0
        self.holdings = {}

        self.refresh()

    def refresh(self):
        # 🔥 TEST에서는 실 API 절대 호출 안 함
        if TEST_MODE:
            return

        raw_cash = get_available_cash(self.token)
        if raw_cash:
            self.cash = min(raw_cash, STRATEGY_MAX_CASH)

        # LIVE에서는 holdings API가 따로 구현돼 있다면 여기서 갱신
        # (현재 구조상 TEST에서는 사용 안 함)

    def has_position(self, symbol: str) -> bool:
        return symbol in self.holdings
