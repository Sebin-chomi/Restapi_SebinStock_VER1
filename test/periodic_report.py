import os
import csv
from datetime import datetime, timedelta
from glob import glob

from config import MAX_MDD_PCT


LOG_DIR = "trade_logs"


def _safe_int(x, default=0):
    try:
        return int(float(x))
    except Exception:
        return default


def _load_daily_pnls():
    """
    return: {date(datetime): pnl(int)}
    """
    pattern = os.path.join(LOG_DIR, "trade_log_*.csv")
    files = sorted(glob(pattern))

    daily = {}

    for path in files:
        base = os.path.basename(path)
        date_str = base.replace("trade_log_", "").replace(".csv", "")

        try:
            d = datetime.strptime(date_str, "%Y%m%d")
        except Exception:
            continue

        day_sum = 0
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                day_sum += _safe_int(row.get("pnl", 0), 0)

        daily[d] = daily.get(d, 0) + day_sum

    return daily


def _calc_mdd(pnls):
    """
    pnls: list[int] (시간 순)
    """
    peak = None
    worst_dd = 0
    running = 0

    for p in pnls:
        running += p
        if peak is None or running > peak:
            peak = running
        dd = (running - peak) / peak if peak and peak != 0 else 0
        worst_dd = min(worst_dd, dd)

    return worst_dd


# ==================================================
# 📊 주간 리포트
# ==================================================
def weekly_report(days=7):
    daily = _load_daily_pnls()
    if not daily:
        return None

    today = datetime.now().date()
    start = today - timedelta(days=days - 1)

    filtered = [(d, p) for d, p in daily.items() if start <= d.date() <= today]
    if not filtered:
        return None

    filtered.sort()
    pnls = [p for _, p in filtered]

    total_pnl = sum(pnls)
    avg_pnl = int(total_pnl / len(pnls))
    mdd = _calc_mdd(pnls)

    return {
        "period": f"최근 {days}일",
        "days": len(pnls),
        "total_pnl": total_pnl,
        "avg_pnl": avg_pnl,
        "mdd": mdd,
        "mdd_limit": MAX_MDD_PCT,
    }


# ==================================================
# 📊 월간 리포트
# ==================================================
def monthly_report(months=1):
    daily = _load_daily_pnls()
    if not daily:
        return None

    today = datetime.now().date()
    start = today.replace(day=1) - timedelta(days=30 * (months - 1))

    filtered = [(d, p) for d, p in daily.items() if d.date() >= start]
    if not filtered:
        return None

    filtered.sort()
    pnls = [p for _, p in filtered]

    total_pnl = sum(pnls)
    avg_pnl = int(total_pnl / len(pnls))
    mdd = _calc_mdd(pnls)

    return {
        "period": f"최근 {months}개월",
        "days": len(pnls),
        "total_pnl": total_pnl,
        "avg_pnl": avg_pnl,
        "mdd": mdd,
        "mdd_limit": MAX_MDD_PCT,
    }
