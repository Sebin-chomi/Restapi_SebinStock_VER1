# ===============================
# test/framework/engine/day_controller.py
# ===============================
import asyncio
from datetime import datetime

from test.market_hour import is_market_open, get_market_open_time
from test.framework.engine.runner import MainApp
from test.framework.record.day_summary import format_day_summary
from test.framework.record.event_notifier import should_notify, format_event_alert
from test.tel_logger import tel_log
from test.framework.watchlist.store import clear_dynamic


class DayController:
    def __init__(self, bot_id: str = "scout_v1"):
        self.bot_id = bot_id
        self.engine = MainApp()

        self.total_scout_count = 0
        self.event_scout_count = 0

        self.fast_interval = 120    # 장 초반 2분
        self.normal_interval = 300  # 이후 5분
        self.fast_duration_sec = 30 * 60  # 장 초반 30분

    async def run(self):
        tel_log(
            title="SYSTEM",
            body="📡 DayController 시작 (정찰 대기)",
        )

        # 장 시작 대기
        while not is_market_open():
            await asyncio.sleep(30)

        market_open_time = get_market_open_time()
        tel_log(
            title="SYSTEM",
            body="🟢 장 시작 감지 → 정찰 시작",
        )

        # 장 중 루프
        while is_market_open():
            now = datetime.now()
            elapsed = (now - market_open_time).total_seconds()

            interval = (
                self.fast_interval
                if elapsed <= self.fast_duration_sec
                else self.normal_interval
            )

            # 정찰 1회 실행
            final_payload = await self.engine.run_once()
            self.total_scout_count += 1

            # 이벤트 알림 (선별)
            if should_notify(final_payload["observations"]):
                self.event_scout_count += 1
                tel_log(
                    title="SCOUT EVENT",
                    body=format_event_alert(
                        meta=final_payload["meta"],
                        observations=final_payload["observations"],
                    ),
                )

            await asyncio.sleep(interval)

        # ===============================
        # 장 종료 처리
        # ===============================
        summary_msg = format_day_summary(
            bot_id=self.bot_id,
            total_count=self.total_scout_count,
            event_count=self.event_scout_count,
        )

        tel_log(
            title="DAY SUMMARY",
            body=summary_msg,
        )

        # 🔚 변동 감시 종목 초기화 (여기가 맞는 위치)
        clear_dynamic()
