# ===============================
# scout_selector/utils/market_calendar.py
# 거래일/휴장일 판단 유틸리티
# ===============================
"""
거래일/휴장일 판단 모듈

역할:
- 특정 날짜가 거래일인지 휴장일인지 판단
- pykrx 기반 판단 (우선순위 1)
- 주말 체크 (우선순위 2)
- 데이터 파일 존재 여부 (우선순위 3, fallback)
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


def is_market_open(date: Optional[str] = None) -> bool:
    """
    거래일 여부 판단
    
    Args:
        date: 날짜 (YYYYMMDD, None이면 오늘)
        
    Returns:
        True: 거래일
        False: 휴장일
    """
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    
    # 날짜 형식 검증
    if len(date) != 8 or not date.isdigit():
        return False
    
    # ==========================================
    # 우선순위 1: 주말 체크 (빠른 스킵)
    # ==========================================
    try:
        year = int(date[:4])
        month = int(date[4:6])
        day = int(date[6:8])
        dt = datetime(year, month, day)
        weekday = dt.weekday()  # 0=월요일, 6=일요일
        
        if weekday >= 5:  # 토요일(5) 또는 일요일(6)
            return False
    except Exception:
        pass  # 날짜 파싱 실패 시 다음 단계로
    
    # ==========================================
    # 우선순위 2: pykrx 캘린더 기반 판단
    # ==========================================
    try:
        from pykrx import stock
        
        # 날짜 형식 변환 (YYYYMMDD -> YYYY-MM-DD)
        date_str = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
        
        # 대형주(삼성전자) 데이터로 거래일 여부 판단
        # 데이터가 있으면 거래일, 없으면 휴장일
        df = stock.get_market_ohlcv_by_date(date_str, date_str, "005930")
        
        if df is not None and not df.empty and len(df) > 0:
            return True  # 거래일
        else:
            return False  # 휴장일
    except ImportError:
        # pykrx가 없으면 다음 단계로
        pass
    except Exception:
        # pykrx 조회 실패 시 다음 단계로
        pass
    
    # ==========================================
    # 우선순위 3: 데이터 파일 존재 여부 (fallback)
    # ==========================================
    try:
        # 프로젝트 루트 기준으로 scout_selector/data 경로 찾기
        current_file = Path(__file__).resolve()
        # scout_selector/utils/market_calendar.py → 프로젝트 루트
        project_root = current_file.parents[2]
        data_dir = project_root / "scout_selector" / "data"
        ohlcv_file = data_dir / f"ohlcv_{date}.csv"
        
        # 파일이 존재하면 거래일로 간주
        if ohlcv_file.exists():
            return True
    except Exception:
        pass
    
    # 모든 방법 실패 시 기본값: 휴장일로 간주 (안전한 선택)
    return False


def get_next_trading_day(date: Optional[str] = None) -> str:
    """
    다음 거래일 반환
    
    Args:
        date: 기준 날짜 (YYYYMMDD, None이면 오늘)
        
    Returns:
        다음 거래일 (YYYYMMDD)
    """
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    
    # 최대 10일 후까지 탐색
    for i in range(1, 11):
        try:
            year = int(date[:4])
            month = int(date[4:6])
            day = int(date[6:8])
            dt = datetime(year, month, day)
            next_dt = dt + timedelta(days=i)
            next_date = next_dt.strftime("%Y%m%d")
            
            if is_market_open(next_date):
                return next_date
        except Exception:
            continue
    
    # 탐색 실패 시 원본 날짜 반환
    return date

