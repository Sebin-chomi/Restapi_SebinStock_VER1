# strategy_state.py

from datetime import datetime
from threading import Lock

# =====================================
# 🔐 내부 저장소
# =====================================
_strategy_state = {}
_lock = Lock()


# =====================================
# 🧱 기본 상태 템플릿
# =====================================
def _empty_state():
    return {
        # ===== 상태 =====
        "state": "NONE",  # NONE / ANCHOR_FOUND / BOX_ACTIVE / BOUGHT / TRAILING_ACTIVE / EXITED / INVALID

        # ===== 기준봉 =====
        "anchor_time": None,
        "anchor_open": None,
        "anchor_close": None,
        "anchor_volume": None,

        # ===== 박스 =====
        "box_high": None,
        "box_low": None,
        "box_start_time": None,

        # ===== 캔들 신호 =====
        "signal_wick_bear": False,
        "signal_three_bull": False,
        "signal_engulf": False,

        # ===== 매수 =====
        "buy_price": None,
        "buy_time": None,

        # ===== 트레일링 =====
        "trailing_active": False,
        "trailing_price": None,

        # ===== 메타 =====
        "last_updated": None
    }


# =====================================
# 📌 상태 조회 / 생성
# =====================================
def get_state(stk_cd):
    with _lock:
        if stk_cd not in _strategy_state:
            _strategy_state[stk_cd] = _empty_state()
        return _strategy_state[stk_cd]


# =====================================
# ✏️ 상태 업데이트 (부분 갱신)
# =====================================
def update_state(stk_cd, **kwargs):
    with _lock:
        if stk_cd not in _strategy_state:
            _strategy_state[stk_cd] = _empty_state()

        for k, v in kwargs.items():
            _strategy_state[stk_cd][k] = v

        _strategy_state[stk_cd]["last_updated"] = datetime.now()


# =====================================
# 🔄 상태 리셋 (종목 1개)
# =====================================
def reset_state(stk_cd):
    with _lock:
        _strategy_state[stk_cd] = _empty_state()


# =====================================
# 🔄 전체 상태 리셋 (장 시작 / 장 마감)
# =====================================
def reset_all_states():
    with _lock:
        _strategy_state.clear()


# =====================================
# 🔍 디버그용 출력
# =====================================
def dump_state(stk_cd):
    with _lock:
        state = _strategy_state.get(stk_cd)
        if not state:
            return f"[{stk_cd}] 상태 없음"
        return f"[{stk_cd}] {state}"
