# ===============================
# test/scout_bot/day_main.py
# ===============================
import sys
import os
import asyncio
import signal
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../..")
)
sys.path.insert(0, PROJECT_ROOT)

from test.framework.engine.day_controller import DayController  # noqa: E402
from test.framework.telegram_handler import send_message  # noqa: E402


def send_shutdown_notification(reason: str = "정상 종료"):
    """프로그램 종료 알림 전송"""
    try:
        from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
        if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "*********":
            return
        if not TELEGRAM_CHAT_ID:
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"🔴 정찰봇 종료\n\n시간: {now}\n사유: {reason}"
        send_message(message)
    except Exception as e:
        print(f"[WARN] 종료 알림 전송 실패: {e}")


if __name__ == "__main__":
    controller = DayController(
        base_interval_minutes=5,   # 기본 정찰
        open_interval_minutes=2,   # 장 초반 촘촘
        open_focus_minutes=30,     # 장 초반 집중
    )

    # 종료 핸들러 등록
    def signal_handler(sig, frame):
        send_shutdown_notification("시그널 수신 (SIGINT/SIGTERM)")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        asyncio.run(controller.run())
        # 정상 종료 (장 마감 후)
        send_shutdown_notification("정상 종료 (장 마감)")
    except KeyboardInterrupt:
        # Ctrl+C로 종료
        send_shutdown_notification("사용자 중단 (KeyboardInterrupt)")
        sys.exit(0)
    except Exception as e:
        # 예외 발생으로 종료
        error_msg = f"예외 발생: {str(e)[:100]}"
        send_shutdown_notification(error_msg)
        raise
