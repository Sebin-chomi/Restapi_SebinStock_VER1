# ===============================
# signals_collector/utils/telegram_notifier.py
# ===============================
"""
텔레그램 알림 유틸리티

수집 실패 시 텔레그램으로 알림 전송
"""
import sys
from pathlib import Path
from typing import Optional

# 프로젝트 루트를 경로에 추가
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import requests
    try:
        from test.tel_send import send_message
        HAS_TELEGRAM = True
    except ImportError:
        try:
            from test.config_test import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
            HAS_TELEGRAM = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
        except ImportError:
            HAS_TELEGRAM = False
except ImportError:
    HAS_TELEGRAM = False


def notify_collection_failure(
    collector_name: str,
    error_message: str,
    date: str,
) -> bool:
    """
    수집 실패 알림 전송
    
    Args:
        collector_name: 수집기 이름 (예: "조건식", "뉴스")
        error_message: 오류 메시지
        date: 날짜 (YYYYMMDD)
    
    Returns:
        전송 성공 여부
    """
    if not HAS_TELEGRAM:
        print(f"⚠️  텔레그램 알림 불가 (설정 없음)")
        return False
    
    try:
        message = (
            f"❌ 신호 수집 실패\n"
            f"수집기: {collector_name}\n"
            f"날짜: {date}\n"
            f"오류: {error_message}\n"
            f"\n"
            f"빈 JSON 파일이 생성되었습니다."
        )
        
        send_message(message)
        return True
    
    except Exception as e:
        print(f"⚠️  텔레그램 알림 전송 실패: {e}")
        return False


def notify_collection_success(
    collector_name: str,
    count: int,
    date: str,
) -> bool:
    """
    수집 성공 알림 전송 (선택적)
    
    Args:
        collector_name: 수집기 이름
        count: 수집된 항목 수
        date: 날짜 (YYYYMMDD)
    
    Returns:
        전송 성공 여부
    """
    # 성공 알림은 기본적으로 비활성화 (필요시 활성화)
    return False











