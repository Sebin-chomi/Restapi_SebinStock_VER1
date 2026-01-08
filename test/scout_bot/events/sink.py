# ===============================
# test/scout_bot/events/sink.py
# 이벤트 출력 (JSONL 로그 + 텔레그램 알림)
# ===============================
"""
이벤트 출력 모듈

역할:
- JSONL 로그 파일에 이벤트 기록
- 텔레그램 알림 발송
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from test.scout_bot.events.definitions import Event
from test.framework.telegram_handler import send_message


# =========================
# JSONL 로그
# =========================

def get_events_log_path(date: Optional[str] = None) -> Path:
    """
    이벤트 로그 파일 경로 반환
    
    Args:
        date: 날짜 (YYYYMMDD, None이면 오늘)
        
    Returns:
        파일 경로
    """
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    
    # 프로젝트 루트 기준으로 scout_bot/output/events 경로 찾기
    current_file = Path(__file__).resolve()
    # test/scout_bot/events/sink.py → 프로젝트 루트
    # parents[0]: events/, parents[1]: scout_bot/, parents[2]: test/, parents[3]: 프로젝트 루트
    project_root = current_file.parents[3]
    output_dir = project_root / "scout_bot" / "output" / "events"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    return output_dir / f"events_{date}.jsonl"


def append_jsonl(event: Event) -> bool:
    """
    JSONL 파일에 이벤트 추가
    
    Args:
        event: 이벤트 객체
        
    Returns:
        성공 여부
    """
    try:
        log_path = get_events_log_path()
        with open(log_path, "a", encoding="utf-8") as f:
            json.dump(event.to_dict(), f, ensure_ascii=False)
            f.write("\n")
        return True
    except Exception as e:
        print(f"[ERROR] 이벤트 JSONL 기록 실패: {e}")
        return False


# =========================
# 텔레그램 알림
# =========================

def format_telegram_message(event: Event) -> str:
    """
    텔레그램 메시지 포맷팅
    
    Args:
        event: 이벤트 객체
        
    Returns:
        포맷팅된 메시지
    """
    time_str = event.occurred_at.strftime("%H:%M")
    
    # 이벤트 타입별 메시지 구성
    lines = [
        f"[SCOUT EVENT] {event.event_type.value}",
        event.symbol,
    ]
    
    # metrics 추가
    metrics = event.metrics
    if metrics:
        for key, value in metrics.items():
            if isinstance(value, float):
                # 소수점 2자리까지
                value_str = f"{value:.2f}"
            elif isinstance(value, int):
                # 큰 숫자는 천단위 구분
                value_str = f"{value:,}"
            else:
                value_str = str(value)
            lines.append(f"{key}: {value_str}")
    
    lines.append(f"time: {time_str}")
    
    return "\n".join(lines)


def send_telegram_notification(event: Event) -> bool:
    """
    텔레그램 알림 발송
    
    Args:
        event: 이벤트 객체
        
    Returns:
        성공 여부
    """
    try:
        message = format_telegram_message(event)
        send_message(message)
        return True
    except Exception as e:
        print(f"[ERROR] 텔레그램 알림 발송 실패: {e}")
        return False


# =========================
# 통합 출력
# =========================

def emit_event(event: Event) -> bool:
    """
    이벤트 출력 (JSONL + 텔레그램)
    
    Args:
        event: 이벤트 객체
        
    Returns:
        성공 여부
    """
    # JSONL 기록
    jsonl_ok = append_jsonl(event)
    
    # 텔레그램 알림
    telegram_ok = send_telegram_notification(event)
    
    return jsonl_ok and telegram_ok

