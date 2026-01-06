# ===============================
# test/scout_bot/day_main.py
# ===============================
import sys
import os
import asyncio

# 프로젝트 루트를 Python 경로에 추가
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, PROJECT_ROOT)

from test.framework.engine.day_controller import DayController

if __name__ == "__main__":
    controller = DayController(
        base_interval_minutes=5,   # 기본 정찰
        open_interval_minutes=2,   # 장 초반 촘촘
        open_focus_minutes=30,     # 장 초반 집중
    )

    asyncio.run(controller.run())
