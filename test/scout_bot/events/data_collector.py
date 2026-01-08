# ===============================
# test/scout_bot/events/data_collector.py
# 이벤트 감지에 필요한 데이터 수집
# ===============================
"""
이벤트 감지에 필요한 데이터 수집

역할:
- volume, turnover, day_high, day_low 등 이벤트 감지에 필요한 데이터 수집
- API 호출 또는 기존 데이터 구조에서 추출
"""
from __future__ import annotations

from typing import Dict, Optional, List
from datetime import datetime

from test.price_api import get_current_price


class EventDataCollector:
    """이벤트 감지용 데이터 수집기"""
    
    def __init__(self, token: str, thresholds: dict = None):
        """
        Args:
            token: API 토큰
            thresholds: 이벤트 임계값 설정 (None이면 설정 파일에서 로드)
        """
        self.token = token
        
        # 설정 로드
        if thresholds is None:
            try:
                from test.scout_bot.config.loaders import load_event_thresholds
                thresholds = load_event_thresholds()
            except Exception:
                # 로드 실패 시 기본값
                from test.scout_bot.config.loaders import DEFAULT_THRESHOLDS
                thresholds = DEFAULT_THRESHOLDS.copy()
        
        self.thresholds = thresholds
        
        # 당일 고가/저가 추적 (런타임 메모리)
        self._day_high_low: Dict[str, Dict[str, float]] = {}  # {symbol: {"high": float, "low": float}}
        # 분봉 거래량 히스토리 (최근 N분)
        self._volume_history: Dict[str, List[float]] = {}  # {symbol: [volume1, volume2, ...]}
        # 분봉 거래대금 히스토리
        self._turnover_history: Dict[str, List[float]] = {}  # {symbol: [turnover1, turnover2, ...]}
    
    def collect_snapshot(self, symbol: str) -> Dict:
        """
        종목의 현재 스냅샷 데이터 수집
        
        Args:
            symbol: 종목 코드
            
        Returns:
            스냅샷 데이터 딕셔너리 (체크리스트 구조)
        """
        from datetime import datetime
        
        try:
            price = get_current_price(symbol, self.token)
            
            if price <= 0:
                # 필수 필드 부족 시 빈 스냅샷 반환
                return {
                    "symbol": symbol,
                    "timestamp": datetime.now(),
                    "price": None,
                    "volume": None,
                    "turnover_krw": None,
                    "day_open": None,
                    "day_high": None,
                    "day_low": None,
                    "prev_close": None,
                    "avg_volume_n": None,
                }
            
            timestamp = datetime.now()
            
            # 당일 시가 추적 (첫 수집 시 현재가를 시가로 기록)
            if symbol not in self._day_high_low:
                self._day_high_low[symbol] = {
                    "high": price,
                    "low": price,
                    "open": price,  # 첫 수집 시 시가
                }
            else:
                # 고가/저가 업데이트
                self._day_high_low[symbol]["high"] = max(
                    self._day_high_low[symbol]["high"],
                    price
                )
                self._day_high_low[symbol]["low"] = min(
                    self._day_high_low[symbol]["low"],
                    price
                )
            
            day_high = self._day_high_low[symbol]["high"]
            day_low = self._day_high_low[symbol]["low"]
            day_open = self._day_high_low[symbol].get("open")
            
            # 거래량/거래대금 수집
            volume = None  # TODO: API에서 분봉 거래량 수집
            turnover_krw = self.get_latest_turnover(symbol)  # None일 수 있음
            
            # 평균 거래량 계산 (warmup 체크 포함)
            avg_volume_n = None
            volume_history = self._volume_history.get(symbol, [])
            window_minutes = self.thresholds.get("volume", {}).get("spike", {}).get("window_minutes", 10)
            min_data_points = max(5, window_minutes // 2)  # 최소 window의 절반 이상 필요
            if len(volume_history) >= min_data_points:
                avg_volume_n = sum(volume_history) / len(volume_history)
            
            # 전일 종가 (일단 None, API 연동 필요)
            prev_close = None  # TODO: API에서 전일 종가 수집
            
            return {
                "symbol": symbol,
                "timestamp": timestamp,
                "price": price,
                "volume": volume,
                "turnover_krw": turnover_krw,
                "day_open": day_open,
                "day_high": day_high,
                "day_low": day_low,
                "prev_close": prev_close,
                "avg_volume_n": avg_volume_n,
            }
        except Exception as e:
            # 예외 발생 시 빈 스냅샷 반환 (프로그램 중단 방지)
            return {
                "symbol": symbol,
                "timestamp": datetime.now(),
                "price": None,
                "volume": None,
                "turnover_krw": None,
                "day_open": None,
                "day_high": None,
                "day_low": None,
                "prev_close": None,
                "avg_volume_n": None,
            }
    
    def update_volume_history(self, symbol: str, volume: float):
        """
        거래량 히스토리 업데이트 (외부에서 호출)
        
        Args:
            symbol: 종목 코드
            volume: 분봉 거래량
        """
        if symbol not in self._volume_history:
            self._volume_history[symbol] = []
        self._volume_history[symbol].append(volume)
        # 최근 N분만 유지 (설정 파일에서 로드)
        window_minutes = self.thresholds.get("volume", {}).get("spike", {}).get("window_minutes", 10)
        if len(self._volume_history[symbol]) > window_minutes:
            self._volume_history[symbol] = self._volume_history[symbol][-window_minutes:]
    
    def update_turnover_history(self, symbol: str, turnover: float):
        """
        거래대금 히스토리 업데이트 (외부에서 호출)
        
        Args:
            symbol: 종목 코드
            turnover: 분봉 거래대금
        """
        if symbol not in self._turnover_history:
            self._turnover_history[symbol] = []
        self._turnover_history[symbol].append(turnover)
        # 최근 N분만 유지 (volume window와 동일)
        window_minutes = self.thresholds.get("volume", {}).get("spike", {}).get("window_minutes", 10)
        if len(self._turnover_history[symbol]) > window_minutes:
            self._turnover_history[symbol] = self._turnover_history[symbol][-window_minutes:]
    
    def calculate_volume_spike_ratio(self, symbol: str, current_volume: float) -> Optional[float]:
        """
        거래량 스파이크 비율 계산
        
        Args:
            symbol: 종목 코드
            current_volume: 현재 분봉 거래량
            
        Returns:
            volume_spike_ratio (None if insufficient data)
        """
        history = self._volume_history.get(symbol, [])
        if len(history) < 5:  # 최소 5분 데이터 필요
            return None
        
        avg_volume = sum(history) / len(history)
        if avg_volume == 0:
            return None
        
        return current_volume / avg_volume
    
    def get_latest_turnover(self, symbol: str) -> Optional[float]:
        """
        최신 거래대금 반환
        
        Args:
            symbol: 종목 코드
            
        Returns:
            최신 거래대금 (None if no data)
        """
        history = self._turnover_history.get(symbol, [])
        if not history:
            return None
        return history[-1]

