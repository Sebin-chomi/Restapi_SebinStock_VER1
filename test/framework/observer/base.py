# test/framework/observer/base.py : 헌법

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseObserver(ABC):
    """
    Observer 공통 인터페이스
    - 판단 ❌
    - 계산 ❌
    - 기록 ⭕
    """

    @abstractmethod
    def on_event(self, event: Dict[str, Any]) -> None:
        """
        Fake Engine으로부터 '사실(event)'을 전달받는다.
        """
        pass

    @abstractmethod
    def get_record(self) -> Dict[str, Any]:
        """
        지금까지 수집한 기록을 반환한다.
        """
        pass

    def reset(self) -> None:
        """
        다음 정찰을 위해 기록 초기화
        (필수는 아니지만 표준으로 둔다)
        """
        pass
