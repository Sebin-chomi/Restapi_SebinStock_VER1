# test/framework/engine/events.py

from enum import Enum, auto


class EventType(Enum):
    """
    Fake Engine ↔ Observer 공용 이벤트 타입
    """

    # 거래량
    VOLUME_SPIKE = auto()

    # 기준봉
    BASE_CANDLE_CONFIRMED = auto()
    BASE_CANDLE_HIGH_LOW_UPDATED = auto()

    # 박스권 (다음 단계)
    BOX_FORMED = auto()
    BOX_UPDATED = auto()

    # 결과
    BREAKOUT_OCCURRED = auto()
    BREAKOUT_FAILED = auto()

    # 환경
    ENV_SNAPSHOT = auto()
