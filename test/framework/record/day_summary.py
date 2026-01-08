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
    event_stats: Dict[str, Any] | None = None,
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

    # 이벤트 통계 추가
    if event_stats:
        lines.append("")
        lines.append("⚡ 이벤트 통계")
        total_events = event_stats.get("total_events", 0)
        lines.append(f"총 이벤트 발생: {total_events}건")
        
        if total_events > 0:
            lines.append("")
            lines.append("📈 이벤트 타입별")
            by_type = event_stats.get("by_type", {})
            # 이벤트 타입별로 정렬 (빈도순)
            sorted_types = sorted(by_type.items(), key=lambda x: x[1], reverse=True)
            for event_type, count in sorted_types:
                lines.append(f"- {event_type}: {count}건")
            
            # 가장 많이 발생한 종목 Top 5
            by_symbol = event_stats.get("by_symbol", {})
            if by_symbol:
                lines.append("")
                lines.append("🏆 이벤트 발생 종목 Top 5")
                sorted_symbols = sorted(by_symbol.items(), key=lambda x: x[1], reverse=True)[:5]
                for symbol, count in sorted_symbols:
                    lines.append(f"- {symbol}: {count}건")
            
            # 시간대별 분포 (있는 경우)
            hourly = event_stats.get("hourly_distribution", {})
            if hourly:
                lines.append("")
                lines.append("🕐 시간대별 분포")
                sorted_hours = sorted(hourly.items())
                for hour, count in sorted_hours:
                    lines.append(f"- {hour:02d}시: {count}건")

    return "\n".join(lines)


# -------------------------------
# 파일 저장 (TXT + JSON)
# -------------------------------
def save_day_summary(
    bot_id: str,
    date: str,
    aggregated: Dict[str, Any],
    summary_text: str,
    event_stats: Dict[str, Any] | None = None,
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
    json_data = {
        "bot_id": bot_id,
        "date": date,
        "generated_at": datetime.now().isoformat(),
        "total_scouts": aggregated.get("total_scouts", 0),
        "aggregated": aggregated,
    }
    
    # 이벤트 통계 추가
    if event_stats:
        json_data["event_stats"] = event_stats
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            json_data,
            f,
            ensure_ascii=False,
            indent=2,
        )

    return txt_path, json_path
