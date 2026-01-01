import os
import csv
from datetime import datetime, timedelta
from glob import glob
import matplotlib.pyplot as plt

LOG_DIR = "trade_logs"
REPORT_DIR = "reports"
os.makedirs(REPORT_DIR, exist_ok=True)


def _safe_int(x, default=0):
    try:
        return int(float(x))
    except Exception:
        return default


def generate_weekly_pnl_graph(days=7):
    """
    최근 days일 누적 PnL 그래프 생성
    return: None or { output_path, total_days, cum_pnl }
    """
    pattern = os.path.join(LOG_DIR, "trade_log_*.csv")
    files = sorted(glob(pattern))

    today = datetime.now().date()
    start_date = today - timedelta(days=days - 1)

    daily = []

    for path in files:
        fname = os.path.basename(path)
        date_str = fname.replace("trade_log_", "").replace(".csv", "")

        try:
            d = datetime.strptime(date_str, "%Y%m%d").date()
        except Exception:
            continue

        if not (start_date <= d <= today):
            continue

        day_sum = 0
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                day_sum += _safe_int(row.get("pnl", 0), 0)

        daily.append((d.strftime("%m-%d"), day_sum))

    if not daily:
        return None

    daily.sort()

    labels = []
    cum = []
    running = 0

    for label, pnl in daily:
        running += pnl
        labels.append(label)
        cum.append(running)

    output_path = os.path.join(REPORT_DIR, "weekly_cumulative_pnl.png")

    plt.figure()
    plt.plot(labels, cum, marker="o")
    plt.title("Weekly Cumulative PnL")
    plt.xlabel("Date")
    plt.ylabel("PnL (KRW)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return {
        "output_path": output_path,
        "total_days": len(cum),
        "cum_pnl": cum[-1],
    }
