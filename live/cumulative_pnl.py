import os
import csv
from datetime import datetime
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


def build_daily_pnl_from_trade_logs():
    """
    trade_logs/trade_log_YYYYMMDD.csv 파일들을 모두 읽어
    { 'YYYYMMDD': 일일PnL } 형태로 집계한다.
    """
    pattern = os.path.join(LOG_DIR, "trade_log_*.csv")
    files = sorted(glob(pattern))

    daily = {}  # date_str -> pnl_sum

    for path in files:
        # 파일명에서 날짜 추출: trade_log_YYYYMMDD.csv
        base = os.path.basename(path)
        try:
            date_str = base.replace("trade_log_", "").replace(".csv", "")
        except Exception:
            continue

        day_sum = 0
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                day_sum += _safe_int(row.get("pnl", 0), 0)

        daily[date_str] = daily.get(date_str, 0) + day_sum

    return dict(sorted(daily.items()))


def generate_cumulative_pnl_chart(output_path=None):
    """
    누적 PnL 그래프를 PNG로 저장하고,
    요약 dict를 반환한다.

    return:
      None (데이터 없음)
      or dict { 'output_path', 'last_date', 'total_days', 'cum_pnl' }
    """
    daily = build_daily_pnl_from_trade_logs()
    if not daily:
        return None

    dates = list(daily.keys())
    daily_pnls = [daily[d] for d in dates]

    cum = []
    running = 0
    for p in daily_pnls:
        running += p
        cum.append(running)

    if output_path is None:
        # reports/cumulative_pnl.png 로 저장
        output_path = os.path.join(REPORT_DIR, "cumulative_pnl.png")

    # ---- Plot (색 지정 안 함: 기본값 사용) ----
    plt.figure()
    plt.plot(dates, cum, marker="o")
    plt.title("Cumulative PnL")
    plt.xlabel("Date (YYYYMMDD)")
    plt.ylabel("PnL (KRW)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return {
        "output_path": output_path,
        "last_date": dates[-1],
        "total_days": len(dates),
        "cum_pnl": cum[-1],
    }

# ======================================================
# 📊 누적 상태 요약 (main / telegram 용)
# ======================================================
def get_cumulative_status():
    """
    trade_logs 기반으로 누적 상태 요약을 반환한다.
    main.py / 텔레그램 / 리포트 공용
    """
    daily = build_daily_pnl_from_trade_logs()
    if not daily:
        return {
            "total_days": 0,
            "cum_pnl": 0,
            "mdd": 0.0,
        }

    dates = list(daily.keys())
    daily_pnls = [daily[d] for d in dates]

    cum = []
    running = 0
    peak = 0
    mdd = 0

    for p in daily_pnls:
        running += p
        cum.append(running)

        if running > peak:
            peak = running

        drawdown = running - peak
        if drawdown < mdd:
            mdd = drawdown

    return {
        "total_days": len(dates),
        "cum_pnl": cum[-1],
        "mdd": mdd,
    }

