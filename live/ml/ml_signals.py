# ml/ml_signals.py
"""
딥러닝 기반 매매 신호 생성 모듈

역할:
- 기존 strategy_signals.py와 통합
- 딥러닝 모델을 활용한 신호 생성
- 하이브리드 접근 (규칙 기반 + 딥러닝)
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple
from ml.feature_engineer import extract_all_features
from ml.model_manager import ModelManager

# 기존 신호 모듈 import (하이브리드 사용)
from strategy_signals import count_buy_signals, explain_buy_signals


# ==================================================
# 전역 모델 매니저
# ==================================================
_model_manager: Optional[ModelManager] = None


def get_model_manager() -> ModelManager:
    """모델 매니저 싱글톤"""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager


# ==================================================
# 딥러닝 기반 매수 신호
# ==================================================
def get_ml_buy_signal(
    candles: List[Dict],
    box_high: float,
    box_low: float,
    avg_volume: float,
    use_hybrid: bool = True,
    ml_threshold: float = 0.6,
) -> Dict[str, float | bool]:
    """
    딥러닝 기반 매수 신호 생성
    
    Args:
        candles: 캔들 리스트
        box_high: 박스 상단 가격
        box_low: 박스 하단 가격
        avg_volume: 평균 거래량
        use_hybrid: 하이브리드 모드 (규칙 기반 + 딥러닝)
        ml_threshold: 딥러닝 신호 임계값 (0.0 ~ 1.0)
    
    Returns:
        dict: {
            "ml_prob": float,  # 딥러닝 확률
            "ml_confidence": float,  # 신뢰도
            "rule_based_count": int,  # 규칙 기반 신호 개수
            "final_signal": bool,  # 최종 매수 신호
            "signal_strength": float,  # 신호 강도 (0.0 ~ 1.0)
        }
    """
    if not candles:
        return {
            "ml_prob": 0.0,
            "ml_confidence": 0.0,
            "rule_based_count": 0,
            "final_signal": False,
            "signal_strength": 0.0,
        }
    
    # 1. Feature 추출
    features = extract_all_features(
        candles,
        lookback=60,
        include_technical=True,
        include_patterns=True,
        include_volume=True,
    )
    
    # 2. 딥러닝 모델 예측
    model_mgr = get_model_manager()
    ml_prob, ml_confidence = model_mgr.get_buy_signal(features)
    
    # 3. 규칙 기반 신호 (기존 로직)
    rule_based_count = count_buy_signals(
        candles,
        box_high=box_high,
        box_low=box_low,
        avg_volume=avg_volume,
    )
    
    # 4. 최종 신호 결정
    if use_hybrid:
        # 하이브리드: 규칙 기반과 딥러닝 모두 고려
        rule_score = min(rule_based_count / 3.0, 1.0)  # 0~1 정규화
        ml_score = ml_prob
        
        # 가중 평균 (규칙 40%, 딥러닝 60%)
        combined_score = 0.4 * rule_score + 0.6 * ml_score
        
        final_signal = combined_score >= ml_threshold
        signal_strength = combined_score
    else:
        # 딥러닝만 사용
        final_signal = ml_prob >= ml_threshold
        signal_strength = ml_prob
    
    return {
        "ml_prob": ml_prob,
        "ml_confidence": ml_confidence,
        "rule_based_count": rule_based_count,
        "final_signal": final_signal,
        "signal_strength": signal_strength,
    }


# ==================================================
# 딥러닝 기반 매도 신호
# ==================================================
def get_ml_sell_signal(
    buy_price: float,
    current_price: float,
    candles: List[Dict],
    holding_duration_minutes: int = 0,
    ml_threshold: float = 0.6,
) -> Dict[str, float | bool]:
    """
    딥러닝 기반 매도 신호 생성
    
    Args:
        buy_price: 매수 가격
        current_price: 현재 가격
        candles: 최근 캔들 리스트
        holding_duration_minutes: 보유 기간 (분)
        ml_threshold: 딥러닝 신호 임계값
    
    Returns:
        dict: {
            "ml_prob": float,  # 딥러닝 확률
            "ml_confidence": float,  # 신뢰도
            "final_signal": bool,  # 최종 매도 신호
            "pnl_ratio": float,  # 손익률
        }
    """
    if not candles or buy_price <= 0:
        return {
            "ml_prob": 0.0,
            "ml_confidence": 0.0,
            "final_signal": False,
            "pnl_ratio": 0.0,
        }
    
    # 1. Feature 추출
    features = extract_all_features(
        candles,
        lookback=60,
        include_technical=True,
        include_patterns=True,
        include_volume=True,
    )
    
    # 2. 딥러닝 모델 예측
    model_mgr = get_model_manager()
    ml_prob, ml_confidence = model_mgr.get_sell_signal(
        buy_price=buy_price,
        current_price=current_price,
        features=features,
        holding_duration_minutes=holding_duration_minutes,
    )
    
    # 3. 손익률 계산
    pnl_ratio = (current_price - buy_price) / buy_price if buy_price > 0 else 0.0
    
    # 4. 최종 신호 결정
    final_signal = ml_prob >= ml_threshold
    
    return {
        "ml_prob": ml_prob,
        "ml_confidence": ml_confidence,
        "final_signal": final_signal,
        "pnl_ratio": pnl_ratio,
    }


# ==================================================
# 종목 우선순위 스코어링
# ==================================================
def score_stock_priority(
    candles: List[Dict],
    box_high: float,
    box_low: float,
    avg_volume: float,
) -> float:
    """
    종목 우선순위 점수 계산 (딥러닝 기반)
    
    Args:
        candles: 캔들 리스트
        box_high: 박스 상단
        box_low: 박스 하단
        avg_volume: 평균 거래량
    
    Returns:
        float: 종목 점수 (0.0 ~ 1.0, 높을수록 우선순위 높음)
    """
    if not candles:
        return 0.0
    
    # Feature 추출
    features = extract_all_features(
        candles,
        lookback=60,
        include_technical=True,
        include_patterns=True,
        include_volume=True,
    )
    
    # 모델 스코어링
    model_mgr = get_model_manager()
    score = model_mgr.get_stock_score(features)
    
    return score


# ==================================================
# 하이브리드 신호 통합 함수
# ==================================================
def get_hybrid_buy_signal(
    candles: List[Dict],
    box_high: float,
    box_low: float,
    avg_volume: float,
    ml_weight: float = 0.6,
    rule_weight: float = 0.4,
    threshold: float = 0.6,
) -> Tuple[bool, Dict]:
    """
    하이브리드 매수 신호 (규칙 기반 + 딥러닝)
    
    Args:
        candles: 캔들 리스트
        box_high: 박스 상단
        box_low: 박스 하단
        avg_volume: 평균 거래량
        ml_weight: 딥러닝 가중치
        rule_weight: 규칙 기반 가중치
        threshold: 최종 신호 임계값
    
    Returns:
        tuple: (최종 신호 여부, 상세 정보 딕셔너리)
    """
    result = get_ml_buy_signal(
        candles=candles,
        box_high=box_high,
        box_low=box_low,
        avg_volume=avg_volume,
        use_hybrid=True,
        ml_threshold=threshold,
    )
    
    return result["final_signal"], result










