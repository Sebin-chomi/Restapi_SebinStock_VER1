# ===============================
# test/framework/engine/runner.py
# ===============================
import sys
import os
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, PROJECT_ROOT)

from test import config_test
sys.modules["config"] = config_test

from test.account.account_state import AccountState
from test.check_n_buy import chk_n_buy
from test.check_n_sell import chk_n_sell
from login import fn_au10001 as get_token

from test.framework.watchlist.store import get_watchlist
from test.framework.record.scout_record import (
    build_scout_record_v2,
    save_scout_record,
)

# 🔽 [추가] 수급 수집기 (기록 전용)
from test.framework.flow.flow_collector import collect_flow


class MainApp:
    def __init__(self):
        self.token = None
        self.account_state = None

        # 🔹 대형주 기준 슬롯 (benchmark)
        self.large_caps = ["005930", "000660"]

    def _build_snapshot(self, stk: str):
        """가격/상태 스냅샷 (구조만, 판단 없음)"""
        return {
            "price_checked": True,
            "high_updated": False,
            "low_updated": False,
        }

    def run_once(self, *, session: str, interval_min: int):
        if not self.token:
            self.token = get_token()
            self.account_state = AccountState(self.token)

        # 🔹 대형주 + 동적 watchlist 병합
        watchlist = list(dict.fromkeys(self.large_caps + get_watchlist()))

        for stk in watchlist:
            buy_obs = chk_n_buy(stk, self.token, self.account_state)
            sell_obs = chk_n_sell(stk, self.token, self.account_state)

            observer_triggered = bool(buy_obs or sell_obs)

            # 🔽 [추가] 기관/외국인 수급 (설명자)
            flow_data = collect_flow(
                stock_code=stk,
                is_large_cap=stk in self.large_caps,
            )

            record = build_scout_record_v2(
                bot_id="scout_v1",
                stock_code=stk,
                session=session,
                interval_min=interval_min,
                is_large_cap=stk in self.large_caps,
                snapshot=self._build_snapshot(stk),
                observer={
                    "triggered": observer_triggered,
                    "buy_signal": bool(buy_obs),
                    "sell_signal": bool(sell_obs),
                },
                no_event_reason=[]
                if observer_triggered
                else ["NO_OBSERVER_TRIGGER"],
                flow=flow_data,   # ✅ 기록만
            )

            save_scout_record(record)
