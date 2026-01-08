# ===============================
# test/scout_bot/events/detector.py
# 이벤트 감지 로직
# ===============================
"""
이벤트 감지 모듈

역할:
- 스냅샷 데이터를 분석하여 이벤트 감지
- 5종 이벤트 타입 감지 (VOLUME_SPIKE, TURNOVER_THRESHOLD, DAY_HIGH_BREAK, DAY_LOW_BREAK, PRICE_JUMP/DROP)
"""
from __future__ import annotations

from typing import List, Optional
from datetime import datetime

from test.scout_bot.events.definitions import (
    Event,
    EventType,
)
from test.scout_bot.events.data_collector import EventDataCollector


class EventDetector:
    """이벤트 감지기"""
    
    def __init__(self, data_collector: EventDataCollector, thresholds: dict = None):
        """
        Args:
            data_collector: 데이터 수집기
            thresholds: 이벤트 임계값 설정 (None이면 설정 파일에서 로드)
        """
        self.data_collector = data_collector
        
        # 설정 로드
        if thresholds is None:
            try:
                from test.scout_bot.config.loaders import load_event_thresholds
                thresholds = load_event_thresholds()
            except Exception:
                # 로드 실패 시 기본값
                from test.scout_bot.config.loaders import DEFAULT_THRESHOLDS
                thresholds = DEFAULT_THRESHOLDS.copy()
        
        self.thresholds = thresholds
        
        # 고가/저가 갱신 추적 (중복 이벤트 방지용)
        self._last_high: dict[str, float] = {}  # {symbol: last_high}
        self._last_low: dict[str, float] = {}  # {symbol: last_low}
    
    def detect_events(self, symbol: str, debug: bool = False) -> List[Event]:
        """
        종목의 이벤트 감지
        
        Args:
            symbol: 종목 코드
            debug: 디버그 로그 출력 여부
            
        Returns:
            감지된 이벤트 리스트
        """
        events = []
        snapshot = self.data_collector.collect_snapshot(symbol)
        occurred_at = snapshot.get("timestamp") or datetime.now()
        
        # 필수 필드: price
        price = snapshot.get("price")
        if price is None:
            if debug:
                print(f"[SCOUT][SKIP] {symbol} - price missing")
            return events
        
        # 스냅샷 필드 추출
        volume = snapshot.get("volume")
        turnover_krw = snapshot.get("turnover_krw")
        day_open = snapshot.get("day_open")
        day_high = snapshot.get("day_high")
        day_low = snapshot.get("day_low")
        prev_close = snapshot.get("prev_close")
        avg_volume_n = snapshot.get("avg_volume_n")
        
        # ==========================================
        # A-1) VOLUME_SPIKE
        # ==========================================
        # 필수: volume, avg_volume_n
        volume_config = self.thresholds.get("volume", {}).get("spike", {})
        if volume_config.get("enabled", True):
            if volume is not None and avg_volume_n is not None:
                if avg_volume_n > 0:  # 0 나눗셈 방지
                    volume_spike_ratio = volume / avg_volume_n
                    ratio_min = volume_config.get("ratio_min", 2.0)
                    if volume_spike_ratio >= ratio_min:
                        events.append(Event(
                            symbol=symbol,
                            event_type=EventType.VOLUME_SPIKE,
                            occurred_at=occurred_at,
                            metrics={
                                "volume_spike_ratio": volume_spike_ratio,
                                "current_volume": volume,
                                "avg_volume_n": avg_volume_n,
                            },
                        ))
            elif debug:
                print(f"[SCOUT][SKIP] {symbol} VOLUME_SPIKE - avg_volume_n is 0")
        elif debug:
            if volume is None:
                print(f"[SCOUT][SKIP] {symbol} VOLUME_SPIKE - volume missing")
            elif avg_volume_n is None:
                print(f"[SCOUT][SKIP] {symbol} VOLUME_SPIKE - avg_volume_n missing (warmup)")
        
        # ==========================================
        # A-2) TURNOVER_THRESHOLD
        # ==========================================
        # 필수: turnover_krw
        turnover_config = self.thresholds.get("turnover", {}).get("threshold", {})
        if turnover_config.get("enabled", True):
            if turnover_krw is not None:
                krw_min = turnover_config.get("krw_min", 10_000_000_000)
                if turnover_krw >= krw_min:
                    events.append(Event(
                        symbol=symbol,
                        event_type=EventType.TURNOVER_THRESHOLD,
                        occurred_at=occurred_at,
                        metrics={
                            "turnover_krw": turnover_krw,
                        },
                    ))
        elif debug:
            print(f"[SCOUT][SKIP] {symbol} TURNOVER_THRESHOLD - turnover_krw missing")
        
        # ==========================================
        # B-1) DAY_HIGH_BREAK
        # ==========================================
        # 필수: price, day_high
        day_range_config = self.thresholds.get("day_range", {})
        high_break_config = day_range_config.get("high_break", {})
        if high_break_config.get("enabled", True):
            if day_high is not None:
                if price >= day_high:
                    # 고가 갱신 시에만 이벤트 발생 (쿨다운과 함께 사용)
                    last_high = self._last_high.get(symbol)
                    if last_high is None or price > last_high:
                        events.append(Event(
                            symbol=symbol,
                            event_type=EventType.DAY_HIGH_BREAK,
                            occurred_at=occurred_at,
                            metrics={
                                "current_price": price,
                                "day_high": day_high,
                            },
                        ))
                        self._last_high[symbol] = price
        elif debug:
            print(f"[SCOUT][SKIP] {symbol} DAY_HIGH_BREAK - day_high missing")
        
        # ==========================================
        # B-2) DAY_LOW_BREAK
        # ==========================================
        # 필수: price, day_low
        low_break_config = day_range_config.get("low_break", {})
        if low_break_config.get("enabled", True):
            if day_low is not None:
                if price <= day_low:
                    # 저가 갱신 시에만 이벤트 발생 (쿨다운과 함께 사용)
                    last_low = self._last_low.get(symbol)
                    if last_low is None or price < last_low:
                        events.append(Event(
                            symbol=symbol,
                            event_type=EventType.DAY_LOW_BREAK,
                            occurred_at=occurred_at,
                            metrics={
                                "current_price": price,
                                "day_low": day_low,
                            },
                        ))
                        self._last_low[symbol] = price
        elif debug:
            print(f"[SCOUT][SKIP] {symbol} DAY_LOW_BREAK - day_low missing")
        
        # ==========================================
        # B-3) PRICE_JUMP / PRICE_DROP
        # ==========================================
        price_config = self.thresholds.get("price", {}).get("jump_drop", {})
        if price_config.get("enabled", True):
            # 기준 가격 우선순위: 설정 파일 > prev_close > day_open
            base_price_type = price_config.get("base_price", "prev_close")
            base_price = None
            base_type = None
            
            if base_price_type == "prev_close" and prev_close is not None:
                base_price = prev_close
                base_type = "prev_close"
            elif base_price_type == "day_open" and day_open is not None:
                base_price = day_open
                base_type = "day_open"
            elif prev_close is not None:  # 설정과 무관하게 fallback
                base_price = prev_close
                base_type = "prev_close"
            elif day_open is not None:
                base_price = day_open
                base_type = "day_open"
            
            if base_price is not None and base_price > 0:
                change_pct = ((price - base_price) / base_price) * 100
                pct_min = price_config.get("pct_min", 3.0)
                
                if change_pct >= pct_min:
                    events.append(Event(
                        symbol=symbol,
                        event_type=EventType.PRICE_JUMP,
                        occurred_at=occurred_at,
                        metrics={
                            "current_price": price,
                            base_type: base_price,
                            "change_pct": change_pct,
                        },
                    ))
                elif change_pct <= -pct_min:
                    events.append(Event(
                        symbol=symbol,
                        event_type=EventType.PRICE_DROP,
                        occurred_at=occurred_at,
                        metrics={
                            "current_price": price,
                            base_type: base_price,
                            "change_pct": change_pct,
                        },
                    ))
            elif debug:
                print(f"[SCOUT][SKIP] {symbol} PRICE_JUMP/DROP - base_price missing (prev_close/day_open)")
        elif debug:
            print(f"[SCOUT][SKIP] {symbol} PRICE_JUMP/DROP - disabled")
        
        return events

