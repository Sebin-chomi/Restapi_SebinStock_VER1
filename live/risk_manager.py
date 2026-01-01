import os

from config import HALT_FLAG_FILE, MAX_MDD_PCT
from cumulative_pnl import build_daily_pnl_from_trade_logs


# ======================================================
# 🛑 자동매매 중단 여부
# ======================================================
def is_trading_halted():
    return os.path.exists(HALT_FLAG_FILE)


# ======================================================
# ▶ 중단 (텔레그램 /pause)
# ======================================================
def halt_trading():
    if not os.path.exists(HALT_FLAG_FILE):
        with open(HALT_FLAG_FILE, "w") as f:
            f.write("HALT")


# ======================================================
# ▶ 중단 해제 (텔레그램 /resume)
# ======================================================
def clear_halt():
    if os.path.exists(HALT_FLAG_FILE):
        os.remove(HALT_FLAG_FILE)


# ======================================================
# 📊 누적 PnL / MDD 요약
# ======================================================
def get_pnl_status():
    daily = build_daily_pnl_from_trade_logs()
    if not daily:
        return None

    cum = []
    running = 0
    for pnl in daily.values():
        running += pnl
        cum.append(running)

    peak = cum[0]
    worst_dd = 0

    for x in cum:
        if x > peak:
            peak = x
        dd = (x - peak) / peak if peak != 0 else 0
        worst_dd = min(worst_dd, dd)

    return {
        "total_days": len(cum),
        "cum_pnl": cum[-1],
        "mdd": worst_dd,
        "mdd_limit": MAX_MDD_PCT,
    }


# ======================================================
# 🚨 MDD 초과 시 자동 중단
# ======================================================
def check_mdd_and_halt():
    status = get_pnl_status()
    if not status:
        return False

    if status["mdd"] <= MAX_MDD_PCT:
        halt_trading()
        return True

    return False
    return False
