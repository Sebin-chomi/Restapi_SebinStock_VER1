# scripts/run_sell_cycle.py
"""
매도 사이클 실행 스크립트

역할:
- 계좌 보유 종목 순회
- 현재가 조회
- 매도 조건 판단
- (선택) 매도 주문 실행
"""

import os
import datetime

from auth.token_manager import get_token
from account.account_state import AccountState
from broker.sell_api import sell_market
from strategy.sell_planner import should_sell, sell_qty
from market.price_provider import get_current_price


# ==================================================
# 🔒 SAFETY SETTINGS
# ==================================================
ENABLE_REAL_ORDER = False   # ⚠️ 실전 매도 시에만 True
RUN_ONCE_PER_DAY = True     # 하루 1회 실행 제한

RUN_FLAG_FILE = "run_sell_cycle.done"


def run_sell_cycle():
    # ==================================================
    # 🔒 하루 1회 실행 제한
    # ==================================================
    if RUN_ONCE_PER_DAY and os.path.exists(RUN_FLAG_FILE):
        print("[SAFE] 이미 오늘 매도 실행됨.")
        return

    # ==================================================
    # 1️⃣ 토큰 발급 & 계좌 상태 생성
    # ==================================================
    token = get_token()
    account = AccountState(token)

    print(f"[INFO] 현재 보유 종목 수: {account.holding_count()}")

    executed = False

    # ==================================================
    # 2️⃣ 보유 종목 순회
    # ==================================================
    for symbol in account.holdings.keys():
        # 현재가 조회 (REST 기반)
        current_price = get_current_price(token, symbol)

        if current_price <= 0:
            print(f"[WARN] {symbol} 현재가 조회 실패")
            continue

        # 매도 판단
        if not should_sell(account, symbol, current_price):
            continue

        qty = sell_qty(account, symbol)
        if qty <= 0:
            continue

        # ==================================================
        # 3️⃣ 매도 실행 / DRY-RUN
        # ==================================================
        if not ENABLE_REAL_ORDER:
            print(
                f"[DRY-RUN] {symbol} / "
                f"현재가: {current_price:,.0f} / 매도 수량: {qty}"
            )
        else:
            result = sell_market(token, symbol, qty)
            print(f"[SELL] {symbol} / {result['msg']}")

        executed = True

    # ==================================================
    # 4️⃣ 결과 처리
    # ==================================================
    if not executed:
        print("[INFO] 오늘 매도 대상 없음")
    else:
        print("[INFO] 매도 사이클 완료")

    # ==================================================
    # 🔒 실행 완료 플래그 기록
    # ==================================================
    if RUN_ONCE_PER_DAY:
        with open(RUN_FLAG_FILE, "w") as f:
            f.write(datetime.datetime.now().isoformat())


if __name__ == "__main__":
    run_sell_cycle()
