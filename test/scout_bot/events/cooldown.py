# ===============================
# test/scout_bot/events/cooldown.py
# 중복 이벤트 쿨다운 관리
# ===============================
"""
중복 이벤트 쿨다운 관리

역할:
- 동일 종목 + 동일 이벤트 타입의 쿨다운 관리
- 쿨다운 내 재발생 이벤트 필터링
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
from test.scout_bot.events.definitions import EventType


class CooldownManager:
    """이벤트 쿨다운 관리자"""
    
    def __init__(self, cooldown_minutes: int = None):
        """
        Args:
            cooldown_minutes: 쿨다운 시간 (분) (None이면 설정 파일에서 로드)
        """
        if cooldown_minutes is None:
            # 설정 파일에서 로드
            try:
                from test.scout_bot.config.loaders import load_event_thresholds
                thresholds = load_event_thresholds()
                cooldown_minutes = thresholds.get("cooldown", {}).get("minutes", 10)
            except Exception:
                # 로드 실패 시 기본값
                cooldown_minutes = 10
        
        self.cooldown_minutes = cooldown_minutes
        # {(symbol, event_type): last_occurred_at}
        self._cooldown_map: Dict[Tuple[str, EventType], datetime] = {}
    
    def is_cooldown(self, symbol: str, event_type: EventType) -> bool:
        """
        쿨다운 중인지 확인
        
        Args:
            symbol: 종목 코드
            event_type: 이벤트 타입
            
        Returns:
            쿨다운 중이면 True
        """
        key = (symbol, event_type)
        last_occurred = self._cooldown_map.get(key)
        
        if last_occurred is None:
            return False
        
        elapsed = (datetime.now() - last_occurred).total_seconds() / 60
        return elapsed < self.cooldown_minutes
    
    def record_event(self, symbol: str, event_type: EventType, occurred_at: datetime):
        """
        이벤트 발생 기록 (쿨다운 시작)
        
        Args:
            symbol: 종목 코드
            event_type: 이벤트 타입
            occurred_at: 발생 시각
        """
        key = (symbol, event_type)
        self._cooldown_map[key] = occurred_at
    
    def cleanup_expired(self):
        """만료된 쿨다운 항목 정리"""
        now = datetime.now()
        expired_keys = [
            key
            for key, last_occurred in self._cooldown_map.items()
            if (now - last_occurred).total_seconds() / 60 >= self.cooldown_minutes
        ]
        for key in expired_keys:
            del self._cooldown_map[key]
    
    def clear(self):
        """모든 쿨다운 초기화"""
        self._cooldown_map.clear()

