import json
import os
from datetime import datetime
from typing import Dict, Any


def save_scout_record(record: Dict[str, Any], base_dir: str = "records") -> str:
    """
    ScoutRecord(dict)를 JSON 파일로 저장
    """
    date = record["meta"]["date"]
    bot_id = record["meta"]["bot_id"]
    stk_cd = record["meta"]["stk_cd"]

    dir_path = os.path.join(base_dir, date, bot_id)
    os.makedirs(dir_path, exist_ok=True)

    timestamp = datetime.now().strftime("%H%M%S")
    filename = f"{stk_cd}_{timestamp}.json"
    file_path = os.path.join(dir_path, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

    return file_path
