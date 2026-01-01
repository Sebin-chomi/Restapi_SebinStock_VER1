# risk_state.py

"""
📉 계좌 단위 리스크 / 손익 상태 관리
- 체결 PnL 누적
- 일중 손익 관리
- MDD 계산 기초 데이터
"""

from datetime import date
from config import MAX_DAILY_MDD_PCT


# ======================================================
# 🔑 내부 상태
# ======================================================
_state = {
    "date": date.today().isoformat(),
    "daily_pnl": 0.0,
    "cum_pnl": 0.0,
    "peak_pnl": 0.0,
    "mdd": 0.0,
}


# ======================================================
# 📈 거래 손익 추가
# ======================================================
def add_trade_pnl(pnl: float):
    """
    매도 체결 시 호출
    """
    _state["daily_pnl"] += pnl
    _state["cum_pnl"] += pnl

    # 최고점 갱신
    if _state["cum_pnl"] > _state["peak_pnl"]:
        _state["peak_pnl"] = _state["cum_pnl"]

    # MDD 계산 (음수 값)
    drawdown = _state["cum_pnl"] - _state["peak_pnl"]
    _state["mdd"] = min(_state["mdd"], drawdown)


# ======================================================
# 📊 상태 조회
# ======================================================
def get_risk_state():
    return _state.copy()


# ======================================================
# 🔄 일일 초기화
# ======================================================
def reset_daily_risk():
    _state["date"] = date.today().isoformat()
    _state["daily_pnl"] = 0.0
    _state["peak_pnl"] = _state["cum_pnl"]
    _state["mdd"] = 0.0
