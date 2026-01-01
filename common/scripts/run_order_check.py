# scripts/run_order_check.py
"""
주문 체결 상태 점검 스크립트
"""

from auth.token_manager import get_token
from broker.order_status_api import get_order_status
from order.order_tracker import OrderTracker


def run_order_check(tracker: OrderTracker):
    token = get_token()

    statuses = get_order_status(token)

    if not statuses:
        print("[INFO] 조회된 주문 없음")
        return

    tracker.update(statuses)

    print("[INFO] 주문 상태 요약:")
    for order_no, info in tracker.orders.items():
        print(
            f"- 주문번호: {order_no} | "
            f"{info['symbol']} | "
            f"체결: {info['filled_qty']} / {info['order_qty']} | "
            f"상태: {info['status']}"
        )


if __name__ == "__main__":
    tracker = OrderTracker()
    run_order_check(tracker)
