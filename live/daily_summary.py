import os
import csv
from datetime import datetime

# 로그 디렉토리
LOG_DIR = "trade_logs"
SUMMARY_DIR = "daily_summary"

os.makedirs(SUMMARY_DIR, exist_ok=True)


def generate_daily_summary(date_str=None):
    """
    하루 손익 요약 생성

    return:
        None (거래 없음)
        or dict {
            date,
            total_trades,
            total_pnl,
            win_rate,
            summary_path
        }
    """
    if date_str is None:
        date_str = datetime.now().strftime("%Y%m%d")

    log_path = os.path.join(LOG_DIR, f"trade_log_{date_str}.csv")

    if not os.path.exists(log_path):
        return None

    total_pnl = 0
    total_trades = 0
    win_count = 0

    with open(log_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            pnl = float(row["pnl"])
            total_pnl += pnl
            total_trades += 1

            if pnl > 0:
                win_count += 1

    win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0

    summary_path = os.path.join(
        SUMMARY_DIR,
        f"daily_summary_{date_str}.csv"
    )

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("date,total_trades,total_pnl,win_rate\n")
        f.write(
            f"{date_str},"
            f"{total_trades},"
            f"{int(total_pnl)},"
            f"{win_rate:.2f}\n"
        )

    return {
        "date": date_str,
        "total_trades": total_trades,
        "total_pnl": int(total_pnl),
        "win_rate": win_rate,
        "summary_path": summary_path,
    }
