# ===============================
# test/framework/record/event_notifier.py
# ===============================
from typing import Dict, Any, List


# -------------------------------
# 이벤트 발생 여부 판단
# -------------------------------
def should_notify(observations: Dict[str, Any]) -> bool:
    """
    관측 결과 중 observer.triggered == True 가 하나라도 있으면 알림
    """
    for _, obs in observations.items():
        observer = obs.get("observer")
        if observer and observer.get("triggered"):
            return True
    return False


# -------------------------------
# 텔레그램 알림 포맷
# -------------------------------
def format_event_alert(
    meta: Dict[str, Any],
    observations: Dict[str, Any],
) -> str:
    lines: List[str] = []

    env = meta.get("env", "UNKNOWN")
    lines.append(f"🚨 SCOUT EVENT ({env})")

    for stock, obs in observations.items():
        observer = obs.get("observer", {})
        if not observer.get("triggered"):
            continue

        slot = obs.get("slot", "UNKNOWN")
        types = observer.get("type", [])

        type_txt = ", ".join(types) if types else "UNSPECIFIED"

        lines.append(
            f"- {stock} [{slot}] → {type_txt}"
        )

    return "\n".join(lines)
