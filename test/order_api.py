# test/order_api.py
# TEST 전용 가짜 주문 API

def buy(symbol: str, qty: int, token: str):
    return {
        "success": True,
        "symbol": symbol,
        "qty": qty,
        "type": "BUY",
        "mode": "TEST",
    }


def sell(symbol: str, qty: int, token: str):
    return {
        "success": True,
        "symbol": symbol,
        "qty": qty,
        "type": "SELL",
        "mode": "TEST",
    }
