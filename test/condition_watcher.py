# ===============================
# test/condition_watcher.py
# ===============================

import time
import requests
from datetime import datetime

# ===============================
# 패키지 기준 import (전부 test 하위)
# ===============================
from test.condition_store import (
    set_stocks,
    get_enter_time,
    remove_stock,
)
from test.condition_stats import record_condition_enter
from test.tel_send import send_message
from test.config import (
    host_url,
    app_key,
    app_secret,
    MAX_CONDITION_STOCKS,
    MAX_WAIT_BEFORE_BUY_SEC,
)
from test.login import fn_au10001 as get_token


CONDITION_NAME = "자동매매_조건식"
CHECK_INTERVAL = 10


def get_condition_list(token):
    url = f"{host_url}/uapi/domestic-stock/v1/conditions"
    headers = {
        "authorization": f"Bearer {token}",
        "appkey": app_key,
        "appsecret": app_secret,
        "tr_id": "HHKST01000300",
    }
    res = requests.get(url, headers=headers, timeout=10)
    res.raise_for_status()
    return res.json().get("output", [])


def run_condition(token, condition_id):
    url = f"{host_url}/uapi/domestic-stock/v1/conditions/search"
    headers = {
        "authorization": f"Bearer {token}",
        "appkey": app_key,
        "appsecret": app_secret,
        "tr_id": "HHKST01000400",
    }
    res = requests.get(
        url,
        headers=headers,
        params={"condition_id": condition_id},
        timeout=10,
    )
    res.raise_for_status()
    return [x["stk_cd"] for x in res.json().get("output", [])]


def condition_watch_loop(interval=CHECK_INTERVAL):
    print("🔍 조건검색 감시 시작")
    token = get_token()

    conds = get_condition_list(token)
    cond_id = next(
        (c["condition_id"] for c in conds if c["condition_name"] == CONDITION_NAME),
        None,
    )

    if not cond_id:
        print(f"❌ 조건식 없음: {CONDITION_NAME}")
        return

    prev_set = set()

    while True:
        try:
            stocks = run_condition(token, cond_id)
            limited = stocks[:MAX_CONDITION_STOCKS]
            curr_set = set(limited)

            # 🆕 신규 진입
            new = curr_set - prev_set
            for stk in new:
                record_condition_enter(stk)

            if new:
                send_message(
                    "📡 [조건검색 신규 진입]\n"
                    + "\n".join(sorted(new))
                )

            set_stocks(limited)
            prev_set = curr_set

            # ⏱ 미체결 제외
            now = datetime.now()
            for stk in list(curr_set):
                enter_time = get_enter_time(stk)
                if not enter_time:
                    continue

                elapsed = (now - enter_time).total_seconds()
                if elapsed >= MAX_WAIT_BEFORE_BUY_SEC:
                    remove_stock(stk)
                    send_message(
                        f"⌛ [조건검색 제외]\n"
                        f"종목: {stk}\n"
                        f"사유: {MAX_WAIT_BEFORE_BUY_SEC // 60}분 미체결"
                    )

            time.sleep(interval)

        except Exception as e:
            print("❌ 조건검색 오류:", e)
            time.sleep(5)
