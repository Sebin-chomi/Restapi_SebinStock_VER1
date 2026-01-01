# condition_stats.py

import csv
import os
from datetime import datetime

LOG_DIR = "stats_logs"
os.makedirs(LOG_DIR, exist_ok=True)

_today = datetime.now().strftime("%Y%m%d")

_condition_enter = set()   # 조건검색 진입 종목
_buy_success = set()       # 매수 성공 종목


def record_condition_enter(stk_cd):
    _condition_enter.add(stk_cd)


def record_buy_success(stk_cd):
    _buy_success.add(stk_cd)


def save_daily_stats():
    """
    하루 종료 시 CSV 저장
    """
    date = datetime.now().strftime("%Y%m%d")
    path = os.path.join(LOG_DIR, f"condition_stats_{date}.csv")

    total_enter = len(_condition_enter)
    total_buy = len(_buy_success)
    success_rate = (total_buy / total_enter * 100) if total_enter > 0 else 0.0

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "condition_enter", "buy_success", "success_rate"])
        writer.writerow([date, total_enter, total_buy, f"{success_rate:.2f}"])

    return {
        "date": date,
        "condition_enter": total_enter,
        "buy_success": total_buy,
        "success_rate": success_rate
    }


def reset_daily_stats():
    _condition_enter.clear()
    _buy_success.clear()
