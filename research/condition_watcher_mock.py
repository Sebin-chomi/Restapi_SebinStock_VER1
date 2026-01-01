# condition_watcher_mock.py

import time
from datetime import datetime

from condition_store import get_stocks, set_stocks
from tel_send import send_message
from stock_name import get_stock_name


# ===============================
# 🧪 모의 조건검색 종목 풀
# ===============================
MOCK_CONDITION_STOCKS = [
    "005930",
    "000660",
    "035420",
]


def _add_stock(stk_cd: str):
    """
    condition_store에 종목 1개 추가 (기존 구조 유지용)
    """
    stocks = set(get_stocks())
    stocks.add(stk_cd)
    set_stocks(list(stocks))


def condition_watch_loop_mock(token=None):
    """
    🔍 모의투자용 조건검색 감시 루프
    - 실제 REST API 호출 ❌
    - 테스트 종목을 시간차로 조건검색 포착처럼 흉내냄
    """

    send_message("🧪 [MOCK] 조건검색 감시 시작")

    # 초기화
    set_stocks([])

    for stk_cd in MOCK_CONDITION_STOCKS:
        now = datetime.now().strftime("%H:%M:%S")

        _add_stock(stk_cd)

        name = get_stock_name(stk_cd, token)

        send_message(
            f"🔔 [MOCK 조건검색]\n"
            f"종목: {name} ({stk_cd})\n"
            f"시간: {now}"
        )

        # 실제 조건검색 간격처럼 대기
        time.sleep(30)

    send_message("🧪 [MOCK] 조건검색 테스트 종목 주입 완료")
