import os
from datetime import datetime

# 로그 저장 폴더
LOG_DIR = "trade_logs"
os.makedirs(LOG_DIR, exist_ok=True)


def log_trade(
    stk_cd,
    buy_price,
    sell_price,
    qty,
    reason,
):
    """
    매매 결과 로그 저장
    """
    today = datetime.now().strftime("%Y%m%d")
    log_path = os.path.join(LOG_DIR, f"trade_log_{today}.csv")

    pnl = (sell_price - buy_price) * qty
    pnl_pct = (sell_price - buy_price) / buy_price * 100

    is_new_file = not os.path.exists(log_path)

    with open(log_path, "a", encoding="utf-8") as f:
        if is_new_file:
            f.write(
                "datetime,stk_cd,qty,buy_price,sell_price,"
                "pnl,pnl_pct,reason\n"
            )

        f.write(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')},"
            f"{stk_cd},"
            f"{qty},"
            f"{buy_price},"
            f"{sell_price},"
            f"{pnl},"
            f"{pnl_pct:.2f},"
            f"{reason}\n"
        )

""" 결과예시
datetime,stk_cd,qty,buy_price,sell_price,pnl,pnl_pct,reason
2025-01-05 10:23:12,005930,1,72000,74200,2200,3.05,TAKE_PROFIT """
