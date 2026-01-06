# ===============================
# test/framework/engine/day_controller.py
# ===============================
import sys
import os
import asyncio
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, PROJECT_ROOT)

# config 모듈 설정 (텔레그램 전송을 위해 필요)
from test import config_test
sys.modules["config"] = config_test

from test.market_hour import MarketHour
from test.framework.engine.runner import MainApp
from test.framework.record.day_summary import format_day_summary
from test.framework.watchlist.store import clear_dynamic, load_watchlist_from_json
from test.framework.telegram_handler import telegram_polling
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
        # 텔레그램 설정 확인
        try:
            from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
            if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "*********":
                print("⚠️  텔레그램 토큰이 설정되지 않았습니다. 알림이 전송되지 않습니다.")
        except Exception as e:
            print(f"⚠️  텔레그램 설정 확인 실패: {e}")
        
        tel_log("SYSTEM", "📡 DayController 시작 (정찰 대기)")
        
        # 오늘의 watchlist JSON 로드 확인
        today_watchlist = load_watchlist_from_json()
        if today_watchlist:
            tel_log(
                "WATCHLIST",
                f"📋 오늘의 watchlist 로드 완료: {len(today_watchlist)} 종목\n{', '.join(today_watchlist[:10])}{'...' if len(today_watchlist) > 10 else ''}"
            )
        else:
            tel_log("WATCHLIST", "⚠️  오늘의 watchlist JSON이 없습니다. Cold Start 모드로 진행합니다.")
            tel_log("WATCHLIST", "💡 텔레그램 /add 명령어로 종목을 추가할 수 있습니다.")

        # 텔레그램 폴링 시작 (백그라운드)
        polling_task = asyncio.create_task(telegram_polling())

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
                total_count=self.total_scout_count,
                event_count=0,
            ),
        )

        clear_dynamic()
