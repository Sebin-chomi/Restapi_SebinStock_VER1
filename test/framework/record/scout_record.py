from datetime import datetime
from typing import Dict, Any


class ScoutRecord:
    """
    정찰봇 단일 실행(1사이클)의 최종 기록 컨테이너
    - 판단 ❌
    - 계산 ❌
    - 구조화 ⭕
    """

    def __init__(self, meta: Dict[str, Any]):
        self.meta = meta
        self.observations: Dict[str, Any] = {}
        self.created_at = datetime.now()

    def attach_observations(self, observations: Dict[str, Any]) -> None:
        """
        ObserverRegistry.collect_records() 결과를 그대로 부착
        """
        self.observations = observations

    def to_dict(self) -> Dict[str, Any]:
        return {
            "meta": self.meta,
            "observations": self.observations,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
