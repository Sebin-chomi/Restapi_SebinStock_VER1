# test/framework/observer/box.py

from typing import Dict, Any, Optional

from test.framework.observer.base import BaseObserver
from test.framework.engine.events import EventType


class BoxObserver(BaseObserver):
    """
    박스권 형성 여부 감시 Observer
    """

    def __init__(self):
        self._formed: bool = False
        self._duration: Optional[str] = None      # "짧음 / 중간 / 김"
        self._touch_count: Optional[str] = None   # "적음 / 보통 / 다수"

    def on_event(self, event: Dict[str, Any]) -> None:
        """
        event 예시:
        {
            "type": EventType.BOX_FORMED,
            "duration": "중간"
        }
        {
            "type": EventType.BOX_UPDATED,
            "touch_count": "다수"
        }
        """
        etype = event.get("type")

        if etype == EventType.BOX_FORMED:
            self._formed = True
            self._duration = event.get("duration")

        elif etype == EventType.BOX_UPDATED:
            self._touch_count = event.get("touch_count")

    def get_record(self) -> Dict[str, Any]:
        return {
            "formed": self._formed,
            "duration": self._duration,
            "touch_count": self._touch_count,
        }

    def reset(self) -> None:
        self._formed = False
        self._duration = None
        self._touch_count = None
