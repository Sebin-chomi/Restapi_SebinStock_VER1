# ===============================
# test/scout_bot/main.py
# ===============================
import asyncio
from test.framework.engine.runner import MainApp


if __name__ == "__main__":
    # 정찰 1회 실행용 (테스트 / 디버깅)
    asyncio.run(MainApp().run())
