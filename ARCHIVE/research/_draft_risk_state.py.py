# risk_state.py
"""
📉 계좌 리스크 상태 관리
- 일중 누적 손익률(PnL) 추적
- MDD 초과 시 자동 거래 중단
- 텔레그램 명령으로만 재가동 가능
"""

from datetime import datetime, date
from threading import Lock

from config import MAX_DAILY_MDD_PCT


# =====================================================
# 🔐 내부 상태 저장소
# =====================================================
_lock = Lock()

_risk_state = {
    "trading_enabled": True,      # 현재 거래 가능 여부
    "day_pnl_pct": 0.0,           # 오늘 누적 손익률
    "mdd_triggered": False,       # MDD 발동 여부
    "last_update": None,          # 마지막 갱신 시각
    "risk_date": date.today(),    # 기준 날짜
}


# =====================================================
# 🔄 날짜 변경 시 리셋
# =====================================================
def _reset_if_new_day():
    today = date.today()
    if _risk_state["risk_date"] != today:
        _risk_state["risk_date"] = today
        _risk_state["day_pnl_pct"] = 0.0
        _risk_state["mdd_triggered"] = False
        _risk_state["trading_enabled"] = True
        _risk_state["last_update"] = None


# =====================================================
# 📊 PnL 누적 (매도 체결 시 호출)
# =====================================================
def add_trade_pnl(pnl_pct: float):
    """
    pnl_pct: 개별 트레이드 손익률 (예: -0.02, +0.015)
    """
    with _lock:
        _reset_if_new_day()

        _risk_state["day_pnl_pct"] += float(pnl_pct)
        _risk_state["last_update"] = datetime.now()

        # MDD 체크
        if _risk_state["day_pnl_pct"] <= MAX_DAILY_MDD_PCT:
            _risk_state["mdd_triggered"] = True
            _risk_state["trading_enabled"] = False


# =====================================================
# 🚦 거래 가능 여부
# =====================================================
def is_trading_enabled() -> bool:
    with _lock:
        _reset_if_new_day()
        return bool(_risk_state["trading_enabled"])


# =====================================================
# 🔓 수동 재가동 (텔레그램 /resume)
# =====================================================
def resume_trading(reset_pnl: bool = False):
    """
    reset_pnl=True 면:
      - 누적 PnL 초기화 후 재개
    reset_pnl=False 면:
      - PnL 유지한 채 거래 재개
    """
    with _lock:
        _reset_if_new_day()

        _risk_state["trading_enabled"] = True
        _risk_state["mdd_triggered"] = False

        if reset_pnl:
            _risk_state["day_pnl_pct"] = 0.0

        _risk_state["last_update"] = datetime.now()


# =====================================================
# 📋 상태 조회 (텔레그램 /status 용)
# =====================================================
def get_risk_status() -> dict:
    with _lock:
        _reset_if_new_day()
        return {
            "trading_enabled": _risk_state["trading_enabled"],
            "day_pnl_pct": _risk_state["day_pnl_pct"],
            "mdd_triggered": _risk_state["mdd_triggered"],
            "risk_date": str(_risk_state["risk_date"]),
            "last_update": str(_risk_state["last_update"]) if _risk_state["last_update"] else None,
        }
