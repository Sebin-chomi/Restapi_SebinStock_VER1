# ===============================
# test/framework/record/day_summary.py
# ===============================
import os
import json
from collections import defaultdict
from typing import Dict, Any, List
from datetime import datetime


# -------------------------------
# 집계
# -------------------------------
def aggregate_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    summary = {
        "total_scouts": len(records),
        "session_count": defaultdict(int),
        "observer_stats": defaultdict(lambda: defaultdict(int)),
    }

    for rec in records:
        meta = rec.get("meta", {})
        session = meta.get("session", "UNKNOWN")
        summary["session_count"][session] += 1

        observations = rec.get("observations", {})
        for _, obs in observations.items():
            for key, val in obs.items():
                summary["observer_stats"][key][val] += 1

    return summary


# -------------------------------
# TXT 포맷 (사람용)
# ⚠️ DayController와 시그니처 맞춤
# -------------------------------
def format_day_summary(
    bot_id: str,
    total_count: int,
    event_count: int,
    aggregated: Dict[str, Any] | None = None,
) -> str:
    lines = []
    today = datetime.now().strftime("%Y-%m-%d")

    lines.append(f"📅 {today} | {bot_id}")
    lines.append(f"총 정찰 횟수: {total_count}")
    lines.append(f"이벤트 발생 정찰: {event_count}")
    lines.append("")

    if aggregated:
        lines.append("🕒 세션별 정찰")
        for session, cnt in aggregated.get("session_count", {}).items():
            lines.append(f"- {session}: {cnt}")

        lines.append("")
        lines.append("📊 Observer 요약")
        for observer, stats in aggregated.get("observer_stats", {}).items():
            parts = [f"{k}:{v}" for k, v in stats.items()]
            lines.append(f"- {observer} → " + ", ".join(parts))

    return "\n".join(lines)


# -------------------------------
# 파일 저장 (TXT + JSON)
# -------------------------------
def save_day_summary(
    bot_id: str,
    date: str,
    aggregated: Dict[str, Any],
    summary_text: str,
):
    base_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../../records/day_summary")
    )

    dir_path = os.path.join(base_dir, date)
    os.makedirs(dir_path, exist_ok=True)

    # TXT (사람용)
    txt_path = os.path.join(dir_path, f"summary_{bot_id}.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(summary_text)

    # JSON (기계용)
    json_path = os.path.join(dir_path, f"summary_{bot_id}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "bot_id": bot_id,
                "date": date,
                "generated_at": datetime.now().isoformat(),
                "total_scouts": aggregated.get("total_scouts", 0),
                "aggregated": aggregated,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    return txt_path, json_path
