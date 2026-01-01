# scripts/run_buy_cycle.py
"""
매수 사이클 실행 스크립트

역할:
- 관심 종목 로드
- 계좌 상태 생성
- 매수 가능 종목 선별
- 종목당 매수 금액 계산
- (선택) 실제 주문 실행
"""

import os
import datetime

from auth.token_manager import get_token
from account.account_state import AccountState
from strategy.utils.watchlist_loader import load_watchlist
from strategy.buy_planner import can_buy_symbol, calc_buy_cash
from broker.order_api import buy_market


# ==================================================
# 🔒 SAFETY SETTINGS (중요)
# ==================================================
ENABLE_REAL_ORDER = False   # ⚠️ 실전 주문 시에만 True
RUN_ONCE_PER_DAY = True     # 하루 1회 실행 제한

RUN_FLAG_FILE = "run_buy_cycle.done"


def run_buy_cycle():
    # ==================================================
    # 🔒 하루 1회 실행 제한
    # ==================================================
    if RUN_ONCE_PER_DAY and os.path.exists(RUN_FLAG_FILE):
        print("[SAFE] 이미 오늘 실행됨. 종료.")
        return

    # ==================================================
    # 1️⃣ 토큰 발급
    # ==================================================
    token = get_token()

    # ==================================================
    # 2️⃣ 계좌 상태 생성
    # ==================================================
    account = AccountState(token)

    print(f"[INFO] D+2 기준 사용 가능 예수금: {account.cash:,}원")
    print(f"[INFO] 현재 보유 종목 수: {account.holding_count()}")

    # ==================================================
    # 3️⃣ 관심 종목 로드
    # ==================================================
    watchlist = load_watchlist()
    print(f"[INFO] 오늘 후보 종목 수: {len(watchlist)}")

    # ==================================================
    # 4️⃣ 매수 후보 선별 및 실행
    # ==================================================
    executed = False

    for symbol in watchlist:
        if not can_buy_symbol(account, symbol):
            continue

        buy_cash = calc_buy_cash(account)
        if buy_cash <= 0:
            continue

        if not ENABLE_REAL_ORDER:
            print(f"[DRY-RUN] {symbol} / 매수 예정 금액: {buy_cash:,}원")
        else:
            result = buy_market(token, symbol, qty=1)
            print(f"[ORDER] {symbol} / {result['msg']}")

        executed = True

    # ==================================================
    # 5️⃣ 결과 처리
    # ==================================================
    if not executed:
        print("[INFO] 오늘 신규 매수 대상 없음")
    else:
        print("[INFO] 매수 사이클 완료")

    # ==================================================
    # 🔒 실행 완료 플래그 기록
    # ==================================================
    if RUN_ONCE_PER_DAY:
        with open(RUN_FLAG_FILE, "w") as f:
            f.write(datetime.datetime.now().isoformat())


if __name__ == "__main__":
    run_buy_cycle()
