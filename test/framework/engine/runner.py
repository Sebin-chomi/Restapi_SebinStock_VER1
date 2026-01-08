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
from test.login import fn_au10001 as get_token

from test.framework.watchlist.store import get_watchlist
from test.framework.record.scout_record import (
    build_scout_record_v2,
    save_scout_record,
)

# 🔽 [추가] 수급 수집기 (기록 전용)
from test.framework.collector.flow_collector import collect_flow_snapshot
from test.price_api import get_current_price
from test.strategy_state import get_state

# 🔽 [추가] 이벤트 시스템
from test.scout_bot.events.data_collector import EventDataCollector
from test.scout_bot.events.detector import EventDetector
from test.scout_bot.events.cooldown import CooldownManager
from test.scout_bot.events.sink import emit_event


class MainApp:
    def __init__(self):
        self.token = None
        self.account_state = None

        # 🔹 대형주 기준 슬롯 (benchmark)
        self.large_caps = ["005930", "000660"]
        
        # 🔹 이전 snapshot 저장 (고가/저가 갱신 판단용)
        self._prev_snapshots = {}  # {stock_code: {"high": float, "low": float}}
        
        # 🔹 [추가] 이벤트 시스템
        self._event_data_collector = None
        self._event_detector = None
        self._cooldown_manager = CooldownManager()

    def _build_snapshot(self, stk: str, token: str):
        """가격/상태 스냅샷 (실제 가격 정보 수집)"""
        try:
            current_price = get_current_price(stk, token)
            if current_price <= 0:
                return {
                    "price_checked": False,
                    "current_price": None,
                    "high_updated": False,
                    "low_updated": False,
                }
            
            # 이전 snapshot과 비교
            prev = self._prev_snapshots.get(stk, {})
            prev_high = prev.get("high")
            prev_low = prev.get("low")
            
            high_updated = prev_high is not None and current_price > prev_high
            low_updated = prev_low is not None and current_price < prev_low
            
            # 현재 snapshot 저장
            self._prev_snapshots[stk] = {
                "high": max(prev_high, current_price) if prev_high is not None else current_price,
                "low": min(prev_low, current_price) if prev_low is not None else current_price,
            }
            
            return {
                "price_checked": True,
                "current_price": current_price,
                "high_updated": high_updated,
                "low_updated": low_updated,
            }
        except Exception as e:
            print(f"⚠️  Snapshot 수집 실패 ({stk}): {e}")
            return {
                "price_checked": False,
                "current_price": None,
                "high_updated": False,
                "low_updated": False,
            }
    
    def _build_box_info(self, stk: str):
        """Box 정보 수집"""
        try:
            state = get_state(stk)
            box_high = state.get("box_high")
            box_low = state.get("box_low")
            box_start_time = state.get("box_start_time")
            
            formed = box_high is not None and box_low is not None
            
            if not formed:
                return {"formed": False}
            
            # Box 지속 시간 계산
            duration = None
            if box_start_time:
                try:
                    if isinstance(box_start_time, str):
                        start_dt = datetime.fromisoformat(box_start_time)
                    else:
                        start_dt = box_start_time
                    elapsed_minutes = (datetime.now() - start_dt).total_seconds() / 60
                    
                    if elapsed_minutes < 30:
                        duration = "짧음"
                    elif elapsed_minutes < 120:
                        duration = "중간"
                    else:
                        duration = "김"
                except Exception:
                    duration = None
            
            return {
                "formed": True,
                "box_high": box_high,
                "box_low": box_low,
                "box_start_time": box_start_time.isoformat() if hasattr(box_start_time, 'isoformat') else str(box_start_time),
                "duration": duration,
            }
        except Exception as e:
            print(f"⚠️  Box 정보 수집 실패 ({stk}): {e}")
            return {"formed": False}
    
    def _build_base_candle_info(self, stk: str):
        """기준봉 정보 수집"""
        try:
            state = get_state(stk)
            anchor_time = state.get("anchor_time")
            anchor_open = state.get("anchor_open")
            anchor_close = state.get("anchor_close")
            anchor_volume = state.get("anchor_volume")
            
            exists = anchor_time is not None
            
            if not exists:
                return {"exists": False}
            
            return {
                "exists": True,
                "anchor_time": anchor_time.isoformat() if hasattr(anchor_time, 'isoformat') else str(anchor_time),
                "anchor_open": anchor_open,
                "anchor_close": anchor_close,
                "anchor_volume": anchor_volume,
            }
        except Exception as e:
            print(f"⚠️  기준봉 정보 수집 실패 ({stk}): {e}")
            return {"exists": False}

    def run_once(self, *, session: str, interval_min: int):
        if not self.token:
            self.token = get_token()
            self.account_state = AccountState(self.token)
            
            # 🔹 [추가] 이벤트 시스템 초기화 (설정 파일 로드)
            try:
                from test.scout_bot.config.loaders import load_event_thresholds
                thresholds = load_event_thresholds()
            except Exception:
                # 로드 실패 시 기본값 사용
                from test.scout_bot.config.loaders import DEFAULT_THRESHOLDS
                thresholds = DEFAULT_THRESHOLDS.copy()
            
            self._event_data_collector = EventDataCollector(self.token, thresholds)
            self._event_detector = EventDetector(self._event_data_collector, thresholds)

        # 🔹 대형주 + 동적 watchlist 병합
        watchlist = list(dict.fromkeys(self.large_caps + get_watchlist()))

        for stk in watchlist:
            buy_obs = chk_n_buy(stk, self.token, self.account_state)
            sell_obs = chk_n_sell(stk, self.token, self.account_state)

            # ✅ 수정: 딕셔너리의 "triggered" 키 값을 확인
            buy_triggered = buy_obs.get("triggered", False) if isinstance(buy_obs, dict) else False
            sell_triggered = sell_obs.get("triggered", False) if isinstance(sell_obs, dict) else False
            observer_triggered = buy_triggered or sell_triggered

            # ✅ 수정: no_event_reason에 실제 reason 포함
            no_event_reasons = []
            if not observer_triggered:
                if buy_obs and isinstance(buy_obs, dict):
                    buy_reason = buy_obs.get("reason")
                    if buy_reason:
                        no_event_reasons.append(f"BUY_{buy_reason}")
                if sell_obs and isinstance(sell_obs, dict):
                    sell_reason = sell_obs.get("reason")
                    if sell_reason:
                        no_event_reasons.append(f"SELL_{sell_reason}")
                if not no_event_reasons:
                    no_event_reasons.append("NO_OBSERVER_TRIGGER")

            # 🔽 [추가] 기관/외국인 수급 (설명자)
            flow_data = collect_flow_snapshot(
                stock_code=stk,
                token=self.token,
                source="MOCK",
            )
            
            # ✅ 추가: Snapshot 정보 수집
            snapshot = self._build_snapshot(stk, self.token)
            
            # ✅ 추가: Box 정보 수집
            box_info = self._build_box_info(stk)
            
            # ✅ 추가: 기준봉 정보 수집
            base_candle_info = self._build_base_candle_info(stk)

            record = build_scout_record_v2(
                bot_id="scout_v1",
                stock_code=stk,
                session=session,
                interval_min=interval_min,
                is_large_cap=stk in self.large_caps,
                snapshot=snapshot,  # ✅ 수정: 실제 snapshot 정보
                observer={
                    "triggered": observer_triggered,
                    "buy_signal": buy_triggered,
                    "sell_signal": sell_triggered,
                },
                base_candle=base_candle_info,  # ✅ 추가: 기준봉 정보
                box=box_info,  # ✅ 추가: Box 정보
                no_event_reason=no_event_reasons,
                flow=flow_data,
            )

            save_scout_record(record)
            
            # 🔹 [추가] 이벤트 감지 및 출력
            try:
                # 이벤트 감지 (데이터 부족 시 조용히 스킵)
                detected_events = self._event_detector.detect_events(stk, debug=False)
                for event in detected_events:
                    # 쿨다운 체크
                    if not self._cooldown_manager.is_cooldown(stk, event.event_type):
                        # 이벤트 출력 (JSONL + 텔레그램)
                        emit_event(event)
                        # 쿨다운 기록
                        self._cooldown_manager.record_event(
                            stk, event.event_type, event.occurred_at
                        )
                
                # 만료된 쿨다운 정리 (주기적으로)
                if len(self._cooldown_manager._cooldown_map) > 100:
                    self._cooldown_manager.cleanup_expired()
            except Exception as e:
                # 예외 발생 시 조용히 스킵 (프로그램 중단 방지)
                # 디버그 모드일 때만 로그 출력
                pass
