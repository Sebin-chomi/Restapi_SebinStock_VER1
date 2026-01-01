# ===============================
# test/framework/record/day_summary.py
# ===============================

def format_day_summary(bot_id: str, total_count: int, event_count: int) -> str:
    return (
        "📊 하루 정찰 요약\n\n"
        f"봇 ID: {bot_id}\n"
        f"총 정찰 횟수: {total_count}\n"
        f"이벤트 발생: {event_count}\n\n"
        "상태: 정상 종료"
    )
