# test/framework/observer/volume.py

from datetime import datetime
from typing import Dict, Any

from test.framework.observer.base import BaseObserver


class VolumeObserver(BaseObserver):
    """
    거래량 이벤트 감시 Observer
    """

    def __init__(self):
        self._occurred = False
        self._time = None

    def on_event(self, event: Dict[str, Any]) -> None:
        """
        event 예시 (아직 합의 단계):
        {
            "type": "VOLUME_SPIKE",
            "time": datetime
        }
        """
        if event.get("type") == "VOLUME_SPIKE":
            self._occurred = True
            self._time = event.get("time")

    def get_record(self) -> Dict[str, Any]:
        return {
            "occurred": self._occurred,
            "time": self._time.strftime("%H:%M") if self._time else None,
        }

    def reset(self) -> None:
        self._occurred = False
        self._time = None
