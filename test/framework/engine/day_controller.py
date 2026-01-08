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
        
        # 전체 watchlist 로드 (JSON + 수동 추가 + 동적)
        from test.framework.watchlist.store import get_watchlist
        from test.framework.watchlist.manual_additions import get_manual_symbols
        
        # 각 소스별 종목 수 확인
        json_watchlist = load_watchlist_from_json()
        manual_symbols = get_manual_symbols()
        total_watchlist = get_watchlist()
        
        # 알림 메시지 구성
        if total_watchlist:
            json_count = len(json_watchlist)
            manual_count = len(manual_symbols)
            total_count = len(total_watchlist)
            
            msg_parts = [f"📋 Watchlist 로드 완료: 총 {total_count} 종목"]
            
            if json_count > 0:
                msg_parts.append(f"  • 자동 선정: {json_count} 종목")
            if manual_count > 0:
                msg_parts.append(f"  • 수동 추가: {manual_count} 종목")
            
            msg_parts.append(f"\n종목: {', '.join(total_watchlist[:15])}")
            if len(total_watchlist) > 15:
                msg_parts.append(f"... 외 {len(total_watchlist) - 15} 종목")
            
            tel_log("WATCHLIST", "\n".join(msg_parts))
        else:
            tel_log("WATCHLIST", "⚠️  Watchlist가 비어있습니다. Cold Start 모드로 진행합니다.")
            tel_log("WATCHLIST", "💡 텔레그램 /add 명령어로 종목을 추가할 수 있습니다.")

        # 텔레그램 폴링 시작 (백그라운드)
        polling_task = asyncio.create_task(telegram_polling())

        try:
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

            # 이벤트 통계 수집
            event_stats = None
            try:
                from test.scout_bot.events.stats import get_daily_event_stats
                today_date = datetime.now().strftime("%Y%m%d")
                event_stats = get_daily_event_stats(today_date)
            except Exception as e:
                print(f"[WARN] 이벤트 통계 수집 실패: {e}")
            
            # 이벤트 발생 횟수 계산
            event_count = event_stats.get("total_events", 0) if event_stats else 0
            
            tel_log(
                "DAY SUMMARY",
                format_day_summary(
                    bot_id=self.bot_id,
                    total_count=self.total_scout_count,
                    event_count=event_count,
                    event_stats=event_stats,
                ),
            )

            clear_dynamic()
            
        except asyncio.CancelledError:
            # 태스크 취소 시
            from test.framework.telegram_handler import send_message
            send_message("🟡 정찰봇 중단됨 (태스크 취소)")
            raise
        except Exception as e:
            # 예외 발생 시
            from test.framework.telegram_handler import send_message
            error_msg = f"🔴 정찰봇 오류 발생\n\n{str(e)[:200]}"
            send_message(error_msg)
            raise
