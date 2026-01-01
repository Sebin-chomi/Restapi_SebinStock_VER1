# ==================================================
# 📦 보유 종목 관리 (단일 진실원)
# ==================================================
# 구조:
# holding_dict = {
#   "005930": {
#       "qty": 1,
#       "buy_price": 72000
#   }
# }
# ==================================================

holding_dict = {}


def add_holding(stk_cd, qty, buy_price):
    """
    체결 완료 후 보유 종목 추가
    """
    holding_dict[stk_cd] = {
        "qty": qty,
        "buy_price": buy_price,
    }
    print(f"📦 보유 추가: {stk_cd} / {qty}주 / 매수가 {buy_price}")


def remove_holding(stk_cd):
    """
    전량 매도 후 보유 종목 제거
    """
    if stk_cd in holding_dict:
        del holding_dict[stk_cd]
        print(f"📦 보유 제거: {stk_cd}")


def get_holding(stk_cd):
    """
    단일 종목 보유 정보 조회
    """
    return holding_dict.get(stk_cd)


def get_all_holdings():
    """
    전체 보유 종목 반환 (복사본)
    """
    return holding_dict.copy()


def reset_all():
    """
    하루 종료 시 전체 보유 초기화
    """
    holding_dict.clear()
    print("📦 전체 보유 초기화")
