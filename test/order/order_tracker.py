# order/order_tracker.py
"""
주문 상태 추적기 (메모리 기반)

역할:
- 주문 상태 저장
- 체결 / 미체결 / 부분체결 관리
- 재주문 / 취소 판단에 사용
"""

class OrderTracker:
    def __init__(self):
        self.orders = {}

    def register(self, order_no: str, symbol: str, qty: int):
        self.orders[order_no] = {
            "symbol": symbol,
            "order_qty": qty,
            "filled_qty": 0,
            "status": "OPEN",
        }

    def update(self, order_status_list):
        for item in order_status_list:
            order_no = item["order_no"]
            if order_no not in self.orders:
                continue

            self.orders[order_no]["filled_qty"] = item["filled_qty"]
            self.orders[order_no]["status"] = item["status"]

    def get_open_orders(self):
        return {
            k: v for k, v in self.orders.items()
            if v["status"] != "FILLED"
        }
