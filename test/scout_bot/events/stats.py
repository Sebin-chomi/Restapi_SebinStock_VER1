# ===============================
# test/scout_bot/events/stats.py
# 이벤트 통계 수집
# ===============================
"""
이벤트 통계 수집 모듈

역할:
- JSONL 이벤트 로그에서 이벤트 읽기
- 이벤트 타입별 통계 집계
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict

from test.scout_bot.events.sink import get_events_log_path
from test.scout_bot.events.definitions import EventType


def load_events_from_jsonl(date: Optional[str] = None) -> List[Dict]:
    """
    JSONL 이벤트 로그에서 이벤트 읽기
    
    Args:
        date: 날짜 (YYYYMMDD, None이면 오늘)
        
    Returns:
        이벤트 딕셔너리 리스트
    """
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    
    log_path = get_events_log_path(date)
    
    if not log_path.exists():
        return []
    
    events = []
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                    events.append(event)
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"[WARN] 이벤트 로그 읽기 실패 ({log_path}): {e}")
    
    return events


def aggregate_event_stats(events: List[Dict]) -> Dict:
    """
    이벤트 통계 집계
    
    Args:
        events: 이벤트 딕셔너리 리스트
        
    Returns:
        통계 딕셔너리
    """
    stats = {
        "total_events": len(events),
        "by_type": defaultdict(int),
        "by_symbol": defaultdict(int),
        "hourly_distribution": defaultdict(int),  # {hour: count}
    }
    
    for event in events:
        event_type = event.get("event_type")
        symbol = event.get("symbol")
        occurred_at = event.get("occurred_at")
        
        if event_type:
            stats["by_type"][event_type] += 1
        
        if symbol:
            stats["by_symbol"][symbol] += 1
        
        # 시간대별 분포
        if occurred_at:
            try:
                # ISO8601 형식 파싱: "2026-01-08T10:15:00+09:00"
                dt = datetime.fromisoformat(occurred_at.replace("+09:00", ""))
                hour = dt.hour
                stats["hourly_distribution"][hour] += 1
            except Exception:
                pass
    
    # defaultdict를 일반 dict로 변환
    stats["by_type"] = dict(stats["by_type"])
    stats["by_symbol"] = dict(stats["by_symbol"])
    stats["hourly_distribution"] = dict(stats["hourly_distribution"])
    
    return stats


def get_daily_event_stats(date: Optional[str] = None) -> Dict:
    """
    일일 이벤트 통계 반환
    
    Args:
        date: 날짜 (YYYYMMDD, None이면 오늘)
        
    Returns:
        통계 딕셔너리
    """
    events = load_events_from_jsonl(date)
    return aggregate_event_stats(events)






