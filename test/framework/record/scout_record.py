# ===============================
# test/framework/record/scout_record.py
# ===============================
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../records/scout")
)
os.makedirs(BASE_DIR, exist_ok=True)


def build_scout_record_v2(
    *,
    bot_id: str,
    stock_code: str,
    session: str,
    interval_min: int,
    is_large_cap: bool = False,
    snapshot: Optional[Dict[str, Any]] = None,
    observer: Optional[Dict[str, Any]] = None,
    base_candle: Optional[Dict[str, Any]] = None,
    box: Optional[Dict[str, Any]] = None,
    outcome: Optional[Dict[str, Any]] = None,
    expectation: Optional[Dict[str, Any]] = None,
    no_event_reason: Optional[List[str]] = None,
    environment: Optional[Dict[str, Any]] = None,
    flow: Optional[Dict[str, Any]] = None,   # 🔽 [추가]
) -> Dict[str, Any]:
    now = datetime.now()

    record = {
        "meta": {
            "schema_version": "v2",
            "bot_id": bot_id,
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "timestamp": now.isoformat(),
            "session": session,
            "stock_code": stock_code,
            "is_large_cap": is_large_cap,
        },

        # 🔹 상태 스냅샷 (항상 기록)
        "snapshot": snapshot or {},

        # 🔹 Observer 결과 (있다/없다)
        "observer": observer or {"triggered": False},

        "base_candle": base_candle or {"exists": False},
        "box": box or {"formed": False},

        # 🔹 결과 / 기대 (오늘은 비워둬도 OK)
        "outcome": outcome or {},
        "expectation": expectation or {},

        # 🔹 이벤트 미발생 사유
        "no_event_reason": no_event_reason or [],

        # 🔹 시장 환경
        "environment": environment or {},

        # 🔹 🔽 수급 정보 (설명자 전용)
        "flow": flow or {
            "foreign": None,
            "institution": None,
        },

        "interval_min": interval_min,
    }

    return record


def save_scout_record(record: Dict[str, Any]) -> str:
    stock = record["meta"]["stock_code"]
    date = record["meta"]["date"]

    dir_path = os.path.join(BASE_DIR, date)
    os.makedirs(dir_path, exist_ok=True)

    file_path = os.path.join(dir_path, f"{stock}.jsonl")

    with open(file_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return file_path
