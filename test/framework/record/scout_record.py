# ===============================
# test/framework/record/scout_record.py
# ===============================
import os
import json
from datetime import datetime
from typing import Dict, Any, List

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../records/scout")
)
os.makedirs(BASE_DIR, exist_ok=True)


# -------------------------------
# Record 생성
# -------------------------------
def build_scout_record_v2(
    *,
    bot_id: str,
    stock_code: str,
    session: str,
    interval_min: int,
    is_large_cap: bool = False,
    snapshot: Dict[str, Any] | None = None,
    observer: Dict[str, Any] | None = None,
    base_candle: Dict[str, Any] | None = None,
    box: Dict[str, Any] | None = None,
    outcome: Dict[str, Any] | None = None,
    expectation: Dict[str, Any] | None = None,
    no_event_reason: List[str] | None = None,
    environment: Dict[str, Any] | None = None,
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
        "snapshot": snapshot or {},
        "observer": observer or {"triggered": False},
        "base_candle": base_candle or {"exists": False},
        "box": box or {"formed": False},
        "outcome": outcome or {},
        "expectation": expectation or {},
        "no_event_reason": no_event_reason or [],
        "environment": environment or {},
        "interval_min": interval_min,
    }

    return record


# -------------------------------
# 저장 (종목별 JSONL)
# -------------------------------
def save_scout_record(record: Dict[str, Any]):
    stock = record["meta"]["stock_code"]
    date = record["meta"]["date"]

    dir_path = os.path.join(BASE_DIR, date)
    os.makedirs(dir_path, exist_ok=True)

    file_path = os.path.join(dir_path, f"{stock}.jsonl")

    with open(file_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return file_path
