# account/account_state.py
"""
AccountState

역할:
- 예수금 + 보유 종목을 하나의 상태로 통합
- 전략 로직은 이 객체만 바라봄
- API 호출 세부사항은 완전히 숨김
- 전략용 자금 상한(STRATEGY_MAX_CASH) 적용
"""

from broker.balance_api import get_available_cash
from broker.holdings_api import get_holdings
from config import STRATEGY_MAX_CASH


class AccountState:
    """
    전략에서 사용하는 계좌 상태 객체
    """

    def __init__(self, token: str):
        self.token = token
        self.cash: int = 0
        self.holdings: dict = {}
        self.refresh()

    # ==================================================
    # 상태 갱신
    # ==================================================
    def refresh(self):
        """
        계좌 상태 최신화
        """
        # 실제 주문 가능 예수금 (D+2 기준)
        raw_cash = get_available_cash(self.token)

        # 🔒 전략용 예수금 상한 적용 (모의 1억 → 전략 300만)
        self.cash = min(raw_cash, STRATEGY_MAX_CASH)

        # 보유 종목
        self.holdings = get_holdings(self.token)

    # ==================================================
    # 조회용 헬퍼 (전략에서 사용)
    # ==================================================
    def has_position(self, symbol: str) -> bool:
        """
        특정 종목 보유 여부
        """
        return symbol in self.holdings

    def position_qty(self, symbol: str) -> int:
        """
        특정 종목 보유 수량
        """
        if symbol not in self.holdings:
            return 0
        return self.holdings[symbol]["qty"]

    def holding_count(self) -> int:
        """
        현재 보유 종목 수
        """
        return len(self.holdings)
