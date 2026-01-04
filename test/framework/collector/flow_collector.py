# ===============================
# test/framework/collector/flow_collector.py
# ===============================
from datetime import datetime
from typing import Dict, Any


def collect_flow_snapshot(
    *,
    stock_code: str,
    token: str | None = None,
    source: str = "MOCK",
) -> Dict[str, Any]:
    """
    기관/외국인 수급 스냅샷 수집 (설명자 전용)
    - 실 API 연동 전까지는 MOCK 반환
    - runner에서 snapshot과 함께 호출
    """

    now = datetime.now()

    # 🔹 MOCK 데이터 (형태 고정용)
    return {
        "foreign": {
            "net_volume": 0,          # signed int
            "net_value": 0,           # KRW, signed int
            "asof_time": now.strftime("%H:%M:%S"),
            "source": source,
        },
        "institution": {
            "net_volume": 0,          # signed int
            "net_value": 0,           # KRW, signed int
            "asof_time": now.strftime("%H:%M:%S"),
            "source": source,
        },
    }
