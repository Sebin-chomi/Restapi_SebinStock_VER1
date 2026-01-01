# ===============================
# test/framework/engine/runner.py
# ===============================
import asyncio
import sys

# ===============================
# TEST config 바인딩 (패키지 기준)
# ===============================
from test import config_test
sys.modules["config"] = config_test

TEST_MODE = config_test.TEST_MODE

print("### RUNNING TEST ENGINE (SCOUT BOT) ###")
print(f"[ENV] {config_test.ENV_NAME}")

# ===============================
# 패키지 기준 import (전부 test 하위)
# ===============================
from test.account.account_state import AccountState
from test.check_n_buy import chk_n_buy
from test.check_n_sell import chk_n_sell
from test.login import fn_au10001 as get_token
from test.tel_logger import tel_log


class MainApp:
    def __init__(self):
        self.token = None
        self.account_state = None

        # 🔚 엔진 종료 플래그
        self.should_stop = False

        # TEST용 종목 (fallback)
        self.tier1 = {"005930": {}}

        # 🔥 TEST 1사이클 완료 플래그
        self.test_cycle_done = False

    async def run(self):
        # 토큰 및 계좌 상태 초기화
        self.token = get_token()
        self.account_state = AccountState(self.token)

        tel_log(
            title="SYSTEM",
            body="🚀 TEST Fake Engine 시작",
        )

        while not self.should_stop:
            # ===============================
            # 🟢 매수 로직
            # ===============================
            for stk in self.tier1.keys():
                chk_n_buy(stk, self.token, self.account_state)

            # ===============================
            # 🔥 TEST: 강제 매도 (1회만)
            # ===============================
            if TEST_MODE and not self.test_cycle_done:
                for stk in self.tier1.keys():
                    tel_log(
                        title="FORCE SELL CALL",
                        body="🧪 TEST 강제 매도 (1회)",
                        stk_cd=stk,
                    )
                    chk_n_sell(stk, self.token, self.account_state)

                # 1사이클 완료 표시
                self.test_cycle_done = True

                # 엔진 종료 신호
                self.should_stop = True

                # 🔥 같은 루프 즉시 종료
                break

            # ===============================
            # 루프 간격
            # ===============================
            await asyncio.sleep(2)

        # ===============================
        # 🛑 종료 로그
        # ===============================
        tel_log(
            title="SYSTEM",
            body="✅ TEST 1사이클 완료 → Fake Engine 정상 종료",
        )
