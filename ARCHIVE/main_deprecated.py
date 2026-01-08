# ⚠️ DEPRECATED
# 이 파일은 더 이상 사용되지 않습니다.
# 실행은 python -m test.scout_bot.main 을 사용하세요.

# ===============================
# test/main.py
# ===============================
import sys
import os
import asyncio
import time

# 프로젝트 루트 경로 설정
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

# TEST config 바인딩
import config_test
sys.modules["config"] = config_test

print("### RUNNING TEST MAIN ###")
print(f"[ENV] {config_test.ENV_NAME}")

from account.account_state import AccountState
from check_n_buy import chk_n_buy
from check_n_sell import chk_n_sell
from config import TEST_MODE
from login import fn_au10001 as get_token
from tel_logger import tel_log


class MainApp:
    def __init__(self):
        self.token = None
        self.account_state = None

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
            body="🚀 trading_loop 시작",
        )

        while True:
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

            # ===============================
            # 루프 간격
            # ===============================
            await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(MainApp().run())
