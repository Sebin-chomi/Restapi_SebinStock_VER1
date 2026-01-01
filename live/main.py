# main.py
import asyncio
import datetime
import time

import requests

# ===============================
# 계좌 상태
# ===============================
from account.account_state import AccountState

# ===============================
# 매수 / 매도
# ===============================
from check_n_buy import chk_n_buy
from check_n_sell import chk_n_sell
from config import HEARTBEAT_INTERVAL_MIN, TEST_MODE, telegram_token
from login import fn_au10001 as get_token

# ===============================
# 리스크 / 설정
# ===============================
from risk_manager import is_trading_halted

# ===============================
# watchlist
# ===============================
from strategy.utils.watchlist_loader import load_watchlist, split_by_tier

# ===============================
# 텔레그램
# ===============================
from tel_command import handle_command, register_app
from tel_logger import tel_log

# ===============================
# Phase 2 fallback watchlist
# ===============================
PHASE2_FALLBACK_SYMBOLS = [
    "005930",  # 삼성전자
    "000660",  # SK하이닉스
    "035420",  # NAVER
]


# =====================================
# ⏰ 장 열림 여부 판단
# =====================================
def is_market_open(now: datetime.datetime) -> bool:
    if now.weekday() >= 5:
        return False
    return (now.hour > 9 or (now.hour == 9 and now.minute >= 0)) and now.hour < 15


class MainApp:
    def __init__(self):
        # 인증 / 계좌
        self.token = None
        self.account_state: AccountState | None = None

        # 텔레그램 상태
        self.last_update_id = None

        # 타이머
        self.last_heartbeat_ts = 0
        self.last_token_refresh_ts = 0

        # watchlist
        self.watchlist = {}
        self.tier1 = {}
        self.tier2 = {}

        # Phase 2: 수동 종목
        self.manual_tier1 = set()

    # =====================================
    # 🔑 토큰 발급
    # =====================================
    async def refresh_token_if_needed(self):
        self.token = get_token()
        self.account_state = AccountState(self.token)
        self.last_token_refresh_ts = time.time()

    # =====================================
    # 🔁 토큰 주기적 갱신
    # =====================================
    async def refresh_token_periodically(self):
        TOKEN_REFRESH_INTERVAL_SEC = 3600

        while True:
            await asyncio.sleep(TOKEN_REFRESH_INTERVAL_SEC)
            try:
                tel_log(title="TOKEN", body="🔄 토큰 자동 갱신")
                await self.refresh_token_if_needed()
                tel_log(title="TOKEN", body="✅ 토큰 갱신 완료")
            except Exception as e:
                tel_log(title="ERROR", body=f"❌ 토큰 갱신 실패\n{e}")
                await asyncio.sleep(60)

    # =====================================
    # 📩 텔레그램 polling (잡음 제거 최종본)
    # =====================================
    async def telegram_polling(self):
        """
        텔레그램 명령 수신 전용 루프 (Phase 2)
        - 네트워크 타임아웃/지연은 조용히 무시
        - 텔레그램에는 매매/시스템 로그만 표시
        """
        url = f"https://api.telegram.org/bot{telegram_token}/getUpdates"

        while True:
            try:
                params = {}
                if self.last_update_id:
                    params["offset"] = self.last_update_id + 1

                res = requests.get(
                    url,
                    params=params,
                    timeout=30,  # 여유 있게
                ).json()

                for update in res.get("result", []):
                    self.last_update_id = update["update_id"]
                    text = update.get("message", {}).get("text")
                    if text:
                        handle_command(text)

                await asyncio.sleep(3)

            except requests.exceptions.ReadTimeout:
                # 텔레그램 서버 응답 지연 → 완전 무시
                await asyncio.sleep(5)

            except requests.exceptions.RequestException as e:
                # 네트워크 계열 문제 → 콘솔 경고만
                print(f"[WARN] telegram_polling network issue: {e}")
                await asyncio.sleep(5)

            except Exception as e:
                # 예상 못한 예외 → 콘솔 경고만
                print(f"[WARN] telegram_polling unexpected error: {e}")
                await asyncio.sleep(5)

    # =====================================
    # 📊 watchlist 로딩 (+ fallback + 수동)
    # =====================================
    def load_today_watchlist(self):
        self.watchlist = load_watchlist()
        self.tier1, self.tier2 = split_by_tier(self.watchlist)

        # Phase 2: Tier1 비어 있으면 fallback
        if TEST_MODE and not self.tier1:
            tel_log(
                title="PHASE2 FALLBACK",
                body="🧪 Tier1 비어 있음 → fallback 종목 자동 주입",
            )
            self.tier1 = {stk: {} for stk in PHASE2_FALLBACK_SYMBOLS}

        # Phase 2: 수동 종목 합집합
        for stk in self.manual_tier1:
            self.tier1.setdefault(stk, {})

        tel_log(
            title="WATCHLIST",
            body=(
                "📋 오늘의 매매 대상\n\n"
                f"- Tier1: {len(self.tier1)} 종목\n"
                f"- Tier2: {len(self.tier2)} 종목\n"
                f"- Manual: {len(self.manual_tier1)} 종목"
            ),
        )

    # =====================================
    # 🧩 Phase 2: 수동 종목 제어 API
    # =====================================
    def add_manual_watch(self, stk_cd: str):
        self.manual_tier1.add(stk_cd)
        tel_log(
            title="MANUAL ADD",
            body=f"➕ 수동 종목 추가: {stk_cd}",
            stk_cd=stk_cd,
        )

    def remove_manual_watch(self, stk_cd: str) -> bool:
        if stk_cd not in self.manual_tier1:
            return False

        self.manual_tier1.remove(stk_cd)
        tel_log(
            title="MANUAL REMOVE",
            body=f"➖ 수동 종목 제거: {stk_cd}",
            stk_cd=stk_cd,
        )
        return True

    def get_manual_watch_list(self):
        return sorted(self.manual_tier1)

    # =====================================
    # 🔁 트레이딩 루프 (Phase 2 핵심)
    # =====================================
    async def trading_loop(self):
        tel_log(title="SYSTEM", body="🚀 Phase 2 trading_loop 시작")

        self.load_today_watchlist()

        while True:
            try:
                if not is_market_open(datetime.datetime.now()):
                    await asyncio.sleep(10)
                    continue

                if is_trading_halted():
                    await asyncio.sleep(30)
                    continue

                # 💓 하트비트
                now_ts = time.time()
                if now_ts - self.last_heartbeat_ts >= HEARTBEAT_INTERVAL_MIN * 60:
                    self.last_heartbeat_ts = now_ts
                    tel_log(title="HEARTBEAT", body="💓 시스템 정상 동작 중")

                # 🔴 매도 우선
                for stk_cd in list(self.account_state.holdings.keys()):
                    chk_n_sell(stk_cd, self.token, self.account_state)

                # 🟢 매수
                for stk_cd in self.tier1.keys():
                    chk_n_buy(stk_cd, self.token, self.account_state)

                await asyncio.sleep(1)

            except Exception as e:
                tel_log(title="ERROR", body=f"❌ trading_loop 오류\n{e}")
                await asyncio.sleep(5)

    # =====================================
    # ▶ 실행 진입점
    # =====================================
    async def run(self):
        register_app(self)
        await self.refresh_token_if_needed()

        await asyncio.gather(
            self.telegram_polling(),
            self.trading_loop(),
            self.refresh_token_periodically(),
        )


# ===============================
# ▶ 프로그램 시작
# ===============================
if __name__ == "__main__":
    app = MainApp()
    asyncio.run(app.run())
