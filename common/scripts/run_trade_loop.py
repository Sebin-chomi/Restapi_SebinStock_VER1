# scripts/run_trade_loop.py
"""
매수 → 매도 순환 루프 스크립트

역할:
1. 매수 사이클 실행
2. 체결 상태 확인
3. 계좌 상태 갱신
4. 매도 조건 판단
5. 매도 실행
"""

import time
import os
import datetime

from auth.token_manager import get_token
from account.account_state import AccountState

from strategy.utils.watchlist_loader import load_watchlist
from strategy.buy_planner import can_buy_symbol, calc_buy_cash
from strategy.sell_planner import should_sell, sell_qty

from broker.order_api import buy_market
from broker.sell_api import sell_market
from broker.order_status_api import get_order_status
from market.price_provider import get_current_price

from tel_send import send_message   # ✅ 텔레그램 전송


# ==================================================
# 🔒 SAFETY SETTINGS
# ==================================================
ENABLE_REAL_ORDER = False      # ⚠️ 실전 주문 시에만 True
RUN_ONCE_PER_DAY = True

RUN_FLAG_FILE = "run_trade_loop.done"

# 체결 대기 시간 (초)
WAIT_AFTER_BUY_SEC = 3


def run_trade_loop():
    try:
        # ==================================================
        # 🔒 하루 1회 실행 제한
        # ==================================================
        if RUN_ONCE_PER_DAY and os.path.exists(RUN_FLAG_FILE):
            print("[SAFE] 이미 오늘 실행됨.")
            return

        # ▶ START 알림
        send_message("[START] trade loop 시작")

        token = get_token()

        # ==================================================
        # 1️⃣ 매수 사이클
        # ==================================================
        account = AccountState(token)
        watchlist = load_watchlist()

        # ▶ 예수금 알림 (가장 중요)
        send_message(f"[CASH] 전략 예수금: {account.cash:,}원")

        print(f"[INFO] 매수 후보 수: {len(watchlist)}")

        buy_orders = []

        for symbol in watchlist:
            if not can_buy_symbol(account, symbol):
                continue

            buy_cash = calc_buy_cash(account)
            if buy_cash <= 0:
                continue

            if not ENABLE_REAL_ORDER:
                print(f"[DRY-RUN][BUY] {symbol} / 예정금액: {buy_cash:,}원")
            else:
                result = buy_market(token, symbol, qty=1)
                print(f"[BUY] {symbol} / {result['msg']}")
                if result.get("success"):
                    buy_orders.append(symbol)

        # ==================================================
        # 2️⃣ 체결 대기
        # ==================================================
        if buy_orders:
            print("[INFO] 체결 대기 중...")
            time.sleep(WAIT_AFTER_BUY_SEC)

        # ==================================================
        # 3️⃣ 계좌 상태 갱신
        # ==================================================
        account.refresh()

        # ==================================================
        # 4️⃣ 매도 판단 & 실행
        # ==================================================
        executed_sell = False

        for symbol in list(account.holdings.keys()):
            current_price = get_current_price(token, symbol)
            if current_price <= 0:
                continue

            if not should_sell(account, symbol, current_price):
                continue

            qty = sell_qty(account, symbol)
            if qty <= 0:
                continue

            if not ENABLE_REAL_ORDER:
                print(
                    f"[DRY-RUN][SELL] {symbol} / "
                    f"현재가: {current_price:,.0f} / 수량: {qty}"
                )
            else:
                result = sell_market(token, symbol, qty)
                print(f"[SELL] {symbol} / {result['msg']}")

            executed_sell = True

        # ==================================================
        # 5️⃣ 결과 요약
        # ==================================================
        if not buy_orders and not executed_sell:
            print("[INFO] 오늘 매수/매도 실행 없음")
            send_message("[END] 매수/매도 실행 없음 (DRY-RUN)")
        else:
            print("[INFO] 매매 사이클 완료")
            send_message("[END] trade loop 정상 종료")

        # ==================================================
        # 🔒 실행 완료 플래그 기록
        # ==================================================
        if RUN_ONCE_PER_DAY:
            with open(RUN_FLAG_FILE, "w") as f:
                f.write(datetime.datetime.now().isoformat())

    except Exception as e:
        # ▶ 의미 있는 에러만 텔레그램으로
        send_message(f"[ERROR] trade loop 실패: {e}")
        raise


if __name__ == "__main__":
    run_trade_loop()
