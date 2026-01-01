# test/framework/observer/base_candle.py

from datetime import datetime
from typing import Dict, Any, Optional

from test.framework.observer.base import BaseObserver


class BaseCandleObserver(BaseObserver):
    """
    기준봉 형성 여부 감시 Observer
    """

    def __init__(self):
        self._formed: bool = False
        self._confirmed_time: Optional[datetime] = None
        self._high_low_updated: bool = False

    def on_event(self, event: Dict[str, Any]) -> None:
        """
        event 예시:
        {
            "type": "BASE_CANDLE_CONFIRMED",
            "time": datetime
        }
        {
            "type": "BASE_CANDLE_HIGH_LOW_UPDATED"
        }
        """
        etype = event.get("type")

        if etype == "BASE_CANDLE_CONFIRMED":
            self._formed = True
            self._confirmed_time = event.get("time")

        elif etype == "BASE_CANDLE_HIGH_LOW_UPDATED":
            # 기준봉 이후 고/저 갱신 여부만 체크
            self._high_low_updated = True

    def get_record(self) -> Dict[str, Any]:
        return {
            "formed": self._formed,
            "confirmed_time": (
                self._confirmed_time.strftime("%H:%M")
                if self._confirmed_time
                else None
            ),
            "high_low_updated": self._high_low_updated,
        }

    def reset(self) -> None:
        self._formed = False
        self._confirmed_time = None
        self._high_low_updated = False
