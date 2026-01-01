# ===============================
# test/scout_bot/day_main.py
# ===============================
import asyncio
from test.framework.engine.day_controller import DayController


if __name__ == "__main__":
    controller = DayController(
        base_interval_minutes=5,   # 기본 정찰
        open_interval_minutes=2,   # 장 초반 촘촘
        open_focus_minutes=30,     # 장 초반 집중 시간
    )
    asyncio.run(controller.run())
