"""
주간 위험 점수 기반 자동 가드
- weekly_error_pnl_analysis_YYYY-WW.csv 기반
- 위험 점수 임계치 초과 시:
  - 텔레그램 경고
  - 자동 매매 중단(halt)
"""

from pathlib import Path
import pandas as pd
from datetime import datetime

from tel_send import send_message
from risk_manager import halt_trading, is_trading_halted
from config import TEST_MODE


BASE_DIR = Path(__file__).resolve().parent
REPORT_DIR = BASE_DIR / "reports"

# ===============================
# 설정값
# ===============================
RISK_SCORE_WARN = 3      # 경고만
RISK_SCORE_HALT = 5      # 자동 중단


def _mode_tag():
    return "🧪 [TEST]" if TEST_MODE else "💰 [REAL]"


def run_risk_guard():
    files = sorted(REPORT_DIR.glob("weekly_error_pnl_analysis_*.csv"))
    if not files:
        return

    src = files[-1]
    df = pd.read_csv(src)
    if df.empty:
        return

    row = df.iloc[0]
    risk_score = int(row["risk_score"])
    notes = row.get("risk_notes", "")

    # ===============================
    # 판단
    # ===============================
    if risk_score >= RISK_SCORE_HALT:
        if not is_trading_halted():
            halt_trading()

            send_message(
                f"{_mode_tag()}\n"
                f"🛑 자동매매 중단 발동\n\n"
                f"- 위험 점수: {risk_score}\n"
                f"- 사유:\n{notes}"
            )

    elif risk_score >= RISK_SCORE_WARN:
        send_message(
            f"{_mode_tag()}\n"
            f"⚠️ 운영 주의 경고\n\n"
            f"- 위험 점수: {risk_score}\n"
            f"- 사유:\n{notes}"
        )


if __name__ == "__main__":
    run_risk_guard()
