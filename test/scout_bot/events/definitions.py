# ===============================
# test/scout_bot/events/definitions.py
# 이벤트 타입 정의 및 설정값
# ===============================
"""
정찰봇 이벤트 타입 정의 및 설정값

역할:
- 이벤트 타입 enum 정의
- 이벤트 감지 기준값 설정
- 이벤트 객체 구조 정의
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime


# =========================
# 이벤트 타입
# =========================

class EventType(str, Enum):
    """이벤트 타입 enum"""
    VOLUME_SPIKE = "VOLUME_SPIKE"
    TURNOVER_THRESHOLD = "TURNOVER_THRESHOLD"
    DAY_HIGH_BREAK = "DAY_HIGH_BREAK"
    DAY_LOW_BREAK = "DAY_LOW_BREAK"
    PRICE_JUMP = "PRICE_JUMP"
    PRICE_DROP = "PRICE_DROP"


# =========================
# 설정값 (YAML에서 로드)
# =========================
# 설정은 test.scout_bot.config.loaders.load_event_thresholds()로 로드
# 기본값은 config/loaders.py의 DEFAULT_THRESHOLDS 참조


# =========================
# 이벤트 객체
# =========================

class Event:
    """이벤트 객체"""
    
    def __init__(
        self,
        symbol: str,
        event_type: EventType,
        occurred_at: datetime,
        metrics: Dict[str, Any],
    ):
        self.symbol = symbol
        self.event_type = event_type
        self.occurred_at = occurred_at
        self.metrics = metrics
    
    def to_dict(self) -> Dict[str, Any]:
        """
        JSON 직렬화용 딕셔너리 변환
        
        occurred_at은 Asia/Seoul 시간대, ISO8601 형식으로 변환
        """
        # Asia/Seoul 시간대 명시 (이미 datetime.now()는 로컬 시간이지만 명시적으로)
        occurred_at_str = self.occurred_at.strftime("%Y-%m-%dT%H:%M:%S+09:00")
        return {
            "symbol": self.symbol,
            "event_type": self.event_type.value,
            "occurred_at": occurred_at_str,
            "metrics": self.metrics,
        }
    
    def __repr__(self) -> str:
        return f"Event({self.symbol}, {self.event_type.value}, {self.occurred_at})"

