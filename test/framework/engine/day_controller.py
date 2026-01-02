# ===============================
# test/framework/engine/day_controller.py
# ===============================
import asyncio
from datetime import datetime

from test.market_hour import MarketHour
from test.framework.engine.runner import MainApp
from test.framework.record.day_summary import format_day_summary
from test.framework.watchlist.store import clear_dynamic
from test.tel_logger import tel_log
from config import DEBUG


class DayController:
    def __init__(
        self,
        bot_id="scout_v1",
        base_interval_minutes=5,
        open_interval_minutes=2,
        open_focus_minutes=30,
    ):
        self.bot_id = bot_id
        self.engine = MainApp()

        self.base_interval = base_interval_minutes * 60
        self.open_interval = open_interval_minutes * 60
        self.open_focus_sec = open_focus_minutes * 60

        self.total_scout_count = 0

    async def run(self):
        tel_log("SYSTEM", "📡 DayController 시작 (정찰 대기)")

        while not MarketHour.is_market_open_time():
            if DEBUG:
                print("[DAY HEARTBEAT] WAIT_MARKET")
            await asyncio.sleep(30)

        market_open_time = datetime.now()

        while MarketHour.is_market_open_time():
            elapsed = (datetime.now() - market_open_time).total_seconds()
            is_open_phase = elapsed <= self.open_focus_sec

            interval = self.open_interval if is_open_phase else self.base_interval
            session = "OPEN" if is_open_phase else "NORMAL"

            if DEBUG:
                print(f"[DAY HEARTBEAT] {session} (interval={interval}s)")

            self.engine.run_once(
                session=session,
                interval_min=interval // 60,
            )

            self.total_scout_count += 1
            await asyncio.sleep(interval)

        tel_log(
            "DAY SUMMARY",
            format_day_summary(
                bot_id=self.bot_id,
                total_scout_count=self.total_scout_count,
                event_scout_count=0,
            ),
        )

        clear_dynamic()
