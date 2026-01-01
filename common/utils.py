import datetime


def is_trade_time():
    now = datetime.datetime.now()
    if now.weekday() >= 5:
        return False
    return 9 <= now.hour < 15
