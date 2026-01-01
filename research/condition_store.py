# condition_store.py

import threading
from datetime import datetime

_target_stocks = set()
_enter_time = {}   # { stk_cd: datetime }
_lock = threading.Lock()


# ==================================================
# 🔄 실전 조건검색용: 전체 리스트 동기화
# ==================================================
def set_stocks(stk_list):
    now = datetime.now()
    with _lock:
        # 신규 진입 종목 시간 기록
        for stk in stk_list:
            if stk not in _target_stocks:
                _enter_time[stk] = now

        # 제거된 종목 정리
        removed = _target_stocks - set(stk_list)
        for stk in removed:
            _enter_time.pop(stk, None)

        _target_stocks.clear()
        for stk in stk_list:
            _target_stocks.add(stk)


# ==================================================
# 🧪 MOCK 조건검색용: 단일 종목 추가
# ==================================================
def add_stock(stk_cd):
    now = datetime.now()
    with _lock:
        if stk_cd not in _target_stocks:
            _target_stocks.add(stk_cd)
            _enter_time[stk_cd] = now


# ==================================================
# 🧹 전체 초기화 (테스트 시작용)
# ==================================================
def clear_stocks():
    with _lock:
        _target_stocks.clear()
        _enter_time.clear()


# ==================================================
# 📥 현재 조건검색 종목
# ==================================================
def get_stocks():
    with _lock:
        return list(_target_stocks)


# ==================================================
# ⏱ 조건검색 진입 시간 조회
# ==================================================
def get_enter_time(stk_cd):
    with _lock:
        return _enter_time.get(stk_cd)


# ==================================================
# ➖ 종목 제거
# ==================================================
def remove_stock(stk_cd):
    with _lock:
        _target_stocks.discard(stk_cd)
        _enter_time.pop(stk_cd, None)


def add_stock(stk_cd):
    now = datetime.now()
    with _lock:
        if stk_cd not in _target_stocks:
            _target_stocks.add(stk_cd)
            _enter_time[stk_cd] = now
