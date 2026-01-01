# test/framework/observer/registry.py

from typing import Dict, Any, List
from test.framework.observer.base import BaseObserver


class ObserverRegistry:
    """
    Observer들을 등록하고, 이벤트를 일괄 전달하는 중앙 허브
    """

    def __init__(self):
        self._observers: List[BaseObserver] = []

    def register(self, observer: BaseObserver) -> None:
        self._observers.append(observer)

    def dispatch(self, event: Dict[str, Any]) -> None:
        """
        모든 Observer에게 이벤트 전달
        """
        for obs in self._observers:
            obs.on_event(event)

    def collect_records(self) -> Dict[str, Any]:
        """
        모든 Observer의 기록 수집
        """
        return {
            obs.__class__.__name__: obs.get_record()
            for obs in self._observers
        }

    def reset_all(self) -> None:
        for obs in self._observers:
            obs.reset()
