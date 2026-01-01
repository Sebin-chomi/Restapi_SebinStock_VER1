# tel_logger.py
"""
텔레그램 로그 전용 모듈 (출력 전용)

원칙
- 시스템 -> 텔레그램 단방향 출력
- 명령 수신(tel_command)과 분리
- 어디서든 안전하게 import 가능하도록 순환 의존성 회피
"""

from datetime import datetime
from typing import Optional

from config import TEST_MODE
from tel_send import send_message


def _now() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _mode_tag() -> str:
    return "🧪 [TEST]" if TEST_MODE else "💰 [REAL]"


def tel_log(
    title: str,
    body: str,
    stk_cd: Optional[str] = None,
    stk_name: Optional[str] = None,
):
    """
    텔레그램 로그 단일 엔트리 포인트

    title: 'SYSTEM', 'LOOP', 'BUY TRY', 'BUY SUCCESS', 'ERROR' 등
    body: 상세 내용(여러 줄 가능)
    stk_cd/stk_name: 종목 정보(없으면 시스템 로그)
    """

    header = f"{_mode_tag()}\n🕒 {_now()}"

    if stk_cd and stk_name:
        header += f"\n📌 {stk_name} ({stk_cd})"

    text = f"{header}\n\n{body}"
    send_message(text)
