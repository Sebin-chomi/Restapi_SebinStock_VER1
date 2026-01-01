# ===============================
# test/framework/engine/runner.py
# ===============================
import sys
import os
import asyncio
from datetime import datetime

# 프로젝트 루트 경로 설정
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, PROJECT_ROOT)

# TEST config 강제 바인딩
from test import config_test
sys.modules["config"] = config_test
TEST_MODE = config_test.TEST_MODE

# Engine / Observer
from test.framework.engine.events import EventType
from test.framework.observer.registry import ObserverRegistry
from test.framework.observer.volume import VolumeObserver
from test.framework.observer.base_candle import BaseCandleObserver
from test.framework.observer.box import BoxObserver

# Record
from test.framework.record.scout_record import ScoutRecord
from test.framework.record.storage import save_scout_record

# Trading / Utils
from test.tel_logger import tel_log
from test.login import fn_au10001 as get_token
from test.account.account_state import AccountState
from test.check_n_buy import chk_n_buy
from test.check_n_sell import chk_n_sell


class MainApp:
    def __init__(self):
        self.token = None
        self.account_state = None

        # 엔진 제어 플래그
        self.should_stop = False
        self.test_cycle_done = False

        # TEST용 종목 (fallback)
        self.tier1 = {"005930": {}}

        # 🔎 Observer Registry (Hook)
        self.registry = ObserverRegistry()
        self.registry.register(VolumeObserver())
        self.registry.register(BaseCandleObserver())
        self.registry.register(BoxObserver())

    async def run(self):
        # 초기화
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
            # 🔔 Fake Event 주입 (정찰용)
            # ===============================
            self.registry.dispatch({
                "type": EventType.VOLUME_SPIKE,
                "time": datetime.now(),
            })

            self.registry.dispatch({
                "type": EventType.BASE_CANDLE_CONFIRMED,
                "time": datetime.now(),
            })

            self.registry.dispatch({
                "type": EventType.BOX_FORMED,
                "duration": "중간",
            })

            # ===============================
            # 🔥 TEST: 강제 매도 (1회)
            # ===============================
            if TEST_MODE and not self.test_cycle_done:
                for stk in self.tier1.keys():
                    chk_n_sell(stk, self.token, self.account_state)

                self.test_cycle_done = True
                self.should_stop = True
                break

            await asyncio.sleep(2)

        # ===============================
        # 📦 정찰 기록 수집 및 통합
        # ===============================
        observations = self.registry.collect_records()

        meta = {
            "bot_id": "scout_v1",
            "stk_cd": list(self.tier1.keys())[0],
            "date": datetime.now().strftime("%Y-%m-%d"),
            "session": "오전",  # ENUM placeholder
        }

        scout_record = ScoutRecord(meta=meta)
        scout_record.attach_observations(observations)
        final_payload = scout_record.to_dict()

        # ===============================
        # 💾 정찰 기록 저장 (JSON)
        # ===============================
        file_path = save_scout_record(final_payload)

        # ===============================
        # 🛑 종료 로그
        # ===============================
        tel_log(
            title="SYSTEM",
            body=(
                "✅ TEST 1사이클 완료 → Fake Engine 정상 종료\n\n"
                f"📁 저장 위치: {file_path}\n\n"
                f"{final_payload}"
            ),
        )


if __name__ == "__main__":
    asyncio.run(MainApp().run())
