# ml/feature_engineer.py
"""
딥러닝 Feature Engineering 모듈

역할:
- OHLCV 데이터로부터 딥러닝 입력 feature 추출
- 기술적 지표 계산 (RSI, MACD, 볼린저 밴드 등)
- 시계열 데이터 전처리 및 정규화
- 캔들 패턴 feature 추출
"""

from __future__ import annotations

from typing import Dict, List, Optional
import numpy as np
import pandas as pd


# ==================================================
# Feature 타입 정의
# ==================================================
Candle = Dict[str, float]  # open/high/low/close/volume


# ==================================================
# 기본 OHLCV Feature 추출
# ==================================================
def extract_ohlcv_features(candles: List[Candle], lookback: int = 60) -> np.ndarray:
    """
    OHLCV 기본 feature 추출
    
    Args:
        candles: 최근 N개 캔들 리스트 (최신이 마지막)
        lookback: 사용할 캔들 개수 (기본 60개 = 5시간)
    
    Returns:
        np.ndarray: shape (lookback, 5) - [open, high, low, close, volume]
    """
    if not candles:
        return np.zeros((lookback, 5))
    
    # 최근 lookback개만 사용
    recent = candles[-lookback:] if len(candles) >= lookback else candles
    
    features = []
    for c in recent:
        features.append([
            float(c.get("open", 0.0)),
            float(c.get("high", 0.0)),
            float(c.get("low", 0.0)),
            float(c.get("close", 0.0)),
            float(c.get("volume", 0.0)),
        ])
    
    # 패딩 (부족한 경우 앞에 0으로 채움)
    if len(features) < lookback:
        padding = [[0.0] * 5] * (lookback - len(features))
        features = padding + features
    
    return np.array(features, dtype=np.float32)


# ==================================================
# 기술적 지표 Feature
# ==================================================
def calculate_rsi(prices: np.ndarray, period: int = 14) -> float:
    """
    RSI (Relative Strength Index) 계산
    
    Args:
        prices: 종가 배열
        period: RSI 기간 (기본 14)
    
    Returns:
        float: RSI 값 (0-100)
    """
    if len(prices) < period + 1:
        return 50.0  # 중립값
    
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return float(rsi)


def calculate_macd(prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
    """
    MACD (Moving Average Convergence Divergence) 계산
    
    Args:
        prices: 종가 배열
        fast: 빠른 이동평균 기간
        slow: 느린 이동평균 기간
        signal: 시그널 라인 기간
    
    Returns:
        dict: {"macd": float, "signal": float, "histogram": float}
    """
    if len(prices) < slow + signal:
        return {"macd": 0.0, "signal": 0.0, "histogram": 0.0}
    
    ema_fast = pd.Series(prices).ewm(span=fast, adjust=False).mean().values
    ema_slow = pd.Series(prices).ewm(span=slow, adjust=False).mean().values
    
    macd_line = ema_fast - ema_slow
    signal_line = pd.Series(macd_line).ewm(span=signal, adjust=False).mean().values
    
    histogram = macd_line[-1] - signal_line[-1]
    
    return {
        "macd": float(macd_line[-1]),
        "signal": float(signal_line[-1]),
        "histogram": float(histogram),
    }


def calculate_bollinger_bands(prices: np.ndarray, period: int = 20, std_dev: float = 2.0) -> Dict[str, float]:
    """
    볼린저 밴드 계산
    
    Args:
        prices: 종가 배열
        period: 이동평균 기간
        std_dev: 표준편차 배수
    
    Returns:
        dict: {"upper": float, "middle": float, "lower": float, "bandwidth": float}
    """
    if len(prices) < period:
        current_price = float(prices[-1]) if len(prices) > 0 else 0.0
        return {
            "upper": current_price,
            "middle": current_price,
            "lower": current_price,
            "bandwidth": 0.0,
        }
    
    recent = prices[-period:]
    middle = np.mean(recent)
    std = np.std(recent)
    
    upper = middle + (std_dev * std)
    lower = middle - (std_dev * std)
    bandwidth = (upper - lower) / middle if middle > 0 else 0.0
    
    return {
        "upper": float(upper),
        "middle": float(middle),
        "lower": float(lower),
        "bandwidth": float(bandwidth),
    }


# ==================================================
# 캔들 패턴 Feature
# ==================================================
def extract_candle_pattern_features(candles: List[Candle]) -> Dict[str, float]:
    """
    캔들 패턴 feature 추출
    
    Args:
        candles: 최근 캔들 리스트
    
    Returns:
        dict: 패턴 feature 딕셔너리
    """
    if not candles or len(candles) < 3:
        return {
            "body_ratio": 0.0,
            "upper_wick_ratio": 0.0,
            "lower_wick_ratio": 0.0,
            "bullish_count": 0.0,
            "bearish_count": 0.0,
            "engulfing_signal": 0.0,
        }
    
    # 최근 5개 캔들 사용
    recent = candles[-5:]
    
    features = []
    for c in recent:
        o = float(c.get("open", 0.0))
        h = float(c.get("high", 0.0))
        l = float(c.get("low", 0.0))
        cl = float(c.get("close", 0.0))
        
        body = abs(cl - o)
        total_range = h - l if h > l else 1.0
        
        upper_wick = max(0.0, h - max(o, cl))
        lower_wick = max(0.0, min(o, cl) - l)
        
        features.append({
            "body_ratio": body / total_range if total_range > 0 else 0.0,
            "upper_wick_ratio": upper_wick / total_range if total_range > 0 else 0.0,
            "lower_wick_ratio": lower_wick / total_range if total_range > 0 else 0.0,
            "is_bullish": 1.0 if cl > o else 0.0,
            "is_bearish": 1.0 if cl < o else 0.0,
        })
    
    # 최근 5개 평균
    avg_body_ratio = np.mean([f["body_ratio"] for f in features])
    avg_upper_wick = np.mean([f["upper_wick_ratio"] for f in features])
    avg_lower_wick = np.mean([f["lower_wick_ratio"] for f in features])
    bullish_count = sum([f["is_bullish"] for f in features])
    bearish_count = sum([f["is_bearish"] for f in features])
    
    # Engulfing 패턴 체크 (최근 2개)
    engulfing = 0.0
    if len(recent) >= 2:
        prev = recent[-2]
        curr = recent[-1]
        prev_o, prev_cl = float(prev.get("open", 0.0)), float(prev.get("close", 0.0))
        curr_o, curr_cl = float(curr.get("open", 0.0)), float(curr.get("close", 0.0))
        
        # Bullish Engulfing
        if prev_cl < prev_o and curr_cl > curr_o:
            if curr_o <= prev_cl and curr_cl >= prev_o:
                engulfing = 1.0
        # Bearish Engulfing
        elif prev_cl > prev_o and curr_cl < curr_o:
            if curr_o >= prev_cl and curr_cl <= prev_o:
                engulfing = -1.0
    
    return {
        "body_ratio": float(avg_body_ratio),
        "upper_wick_ratio": float(avg_upper_wick),
        "lower_wick_ratio": float(avg_lower_wick),
        "bullish_count": float(bullish_count),
        "bearish_count": float(bearish_count),
        "engulfing_signal": float(engulfing),
    }


# ==================================================
# 거래량 Feature
# ==================================================
def extract_volume_features(candles: List[Candle], period: int = 20) -> Dict[str, float]:
    """
    거래량 관련 feature 추출
    
    Args:
        candles: 캔들 리스트
        period: 평균 거래량 계산 기간
    
    Returns:
        dict: 거래량 feature
    """
    if not candles:
        return {
            "volume_ratio": 1.0,
            "volume_trend": 0.0,
            "volume_ma_ratio": 1.0,
        }
    
    volumes = [float(c.get("volume", 0.0)) for c in candles]
    
    if len(volumes) < 2:
        return {
            "volume_ratio": 1.0,
            "volume_trend": 0.0,
            "volume_ma_ratio": 1.0,
        }
    
    current_volume = volumes[-1]
    prev_volume = volumes[-2] if len(volumes) >= 2 else current_volume
    
    # 거래량 변화율
    volume_ratio = current_volume / prev_volume if prev_volume > 0 else 1.0
    
    # 거래량 추세 (최근 5개 평균 vs 이전 5개 평균)
    if len(volumes) >= 10:
        recent_avg = np.mean(volumes[-5:])
        prev_avg = np.mean(volumes[-10:-5])
        volume_trend = (recent_avg - prev_avg) / prev_avg if prev_avg > 0 else 0.0
    else:
        volume_trend = 0.0
    
    # 이동평균 대비 비율
    if len(volumes) >= period:
        volume_ma = np.mean(volumes[-period:])
        volume_ma_ratio = current_volume / volume_ma if volume_ma > 0 else 1.0
    else:
        volume_ma_ratio = 1.0
    
    return {
        "volume_ratio": float(volume_ratio),
        "volume_trend": float(volume_trend),
        "volume_ma_ratio": float(volume_ma_ratio),
    }


# ==================================================
# 통합 Feature 추출 (메인 함수)
# ==================================================
def extract_all_features(
    candles: List[Candle],
    lookback: int = 60,
    include_technical: bool = True,
    include_patterns: bool = True,
    include_volume: bool = True,
) -> Dict[str, np.ndarray | float]:
    """
    모든 feature를 통합하여 추출
    
    Args:
        candles: 캔들 리스트
        lookback: 시계열 feature 길이
        include_technical: 기술적 지표 포함 여부
        include_patterns: 캔들 패턴 포함 여부
        include_volume: 거래량 feature 포함 여부
    
    Returns:
        dict: 모든 feature를 포함한 딕셔너리
    """
    features = {}
    
    # 1. 기본 OHLCV 시계열
    features["ohlcv_sequence"] = extract_ohlcv_features(candles, lookback=lookback)
    
    if not candles:
        return features
    
    # 2. 기술적 지표
    if include_technical:
        closes = np.array([float(c.get("close", 0.0)) for c in candles])
        
        rsi = calculate_rsi(closes)
        macd_dict = calculate_macd(closes)
        bb_dict = calculate_bollinger_bands(closes)
        
        features["rsi"] = rsi
        features["macd"] = macd_dict["macd"]
        features["macd_signal"] = macd_dict["signal"]
        features["macd_histogram"] = macd_dict["histogram"]
        features["bb_upper"] = bb_dict["upper"]
        features["bb_middle"] = bb_dict["middle"]
        features["bb_lower"] = bb_dict["lower"]
        features["bb_bandwidth"] = bb_dict["bandwidth"]
    
    # 3. 캔들 패턴
    if include_patterns:
        pattern_features = extract_candle_pattern_features(candles)
        features.update(pattern_features)
    
    # 4. 거래량 feature
    if include_volume:
        volume_features = extract_volume_features(candles)
        features.update(volume_features)
    
    return features


# ==================================================
# Feature 정규화
# ==================================================
def normalize_features(features: Dict[str, np.ndarray | float], method: str = "minmax") -> Dict[str, np.ndarray | float]:
    """
    Feature 정규화
    
    Args:
        features: 원본 feature 딕셔너리
        method: 정규화 방법 ("minmax" 또는 "zscore")
    
    Returns:
        dict: 정규화된 feature 딕셔너리
    """
    normalized = {}
    
    for key, value in features.items():
        if isinstance(value, np.ndarray):
            if method == "minmax":
                # Min-Max 정규화
                min_val = np.min(value)
                max_val = np.max(value)
                if max_val > min_val:
                    normalized[key] = (value - min_val) / (max_val - min_val)
                else:
                    normalized[key] = value
            elif method == "zscore":
                # Z-score 정규화
                mean_val = np.mean(value)
                std_val = np.std(value)
                if std_val > 0:
                    normalized[key] = (value - mean_val) / std_val
                else:
                    normalized[key] = value
            else:
                normalized[key] = value
        else:
            # 스칼라는 그대로 유지 (모델에서 별도 처리)
            normalized[key] = value
    
    return normalized

