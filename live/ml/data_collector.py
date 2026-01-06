# ml/data_collector.py
"""
딥러닝 학습용 데이터 수집 모듈

역할:
- 실전 거래 데이터 수집
- Feature와 라벨(매수/매도 결과) 저장
- 학습 데이터셋 구축
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from ml.feature_engineer import extract_all_features


# ==================================================
# 데이터 저장 경로
# ==================================================
DATA_DIR = "ml_data"
BUY_DATA_DIR = os.path.join(DATA_DIR, "buy")
SELL_DATA_DIR = os.path.join(DATA_DIR, "sell")
SCORING_DATA_DIR = os.path.join(DATA_DIR, "scoring")


# ==================================================
# 매수 데이터 수집
# ==================================================
def collect_buy_data(
    symbol: str,
    candles: List[Dict],
    box_high: float,
    box_low: float,
    avg_volume: float,
    buy_price: Optional[float] = None,
    buy_time: Optional[datetime] = None,
    label: Optional[bool] = None,  # True: 수익, False: 손실, None: 미정
) -> str:
    """
    매수 시점 데이터 수집
    
    Args:
        symbol: 종목 코드
        candles: 매수 시점의 캔들 리스트
        box_high: 박스 상단
        box_low: 박스 하단
        avg_volume: 평균 거래량
        buy_price: 매수 가격 (있는 경우)
        buy_time: 매수 시간 (있는 경우)
        label: 라벨 (수익/손실, 나중에 업데이트 가능)
    
    Returns:
        str: 저장된 파일 경로
    """
    os.makedirs(BUY_DATA_DIR, exist_ok=True)
    
    # Feature 추출
    features = extract_all_features(
        candles,
        lookback=60,
        include_technical=True,
        include_patterns=True,
        include_volume=True,
    )
    
    # 데이터 구조
    data = {
        "symbol": symbol,
        "timestamp": datetime.now().isoformat(),
        "buy_time": buy_time.isoformat() if buy_time else None,
        "buy_price": buy_price,
        "box_high": box_high,
        "box_low": box_low,
        "avg_volume": avg_volume,
        "features": _serialize_features(features),
        "label": label,  # 나중에 업데이트
        "outcome": None,  # 최종 결과 (수익률 등)
    }
    
    # 파일 저장
    filename = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(BUY_DATA_DIR, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return filepath


# ==================================================
# 매도 데이터 수집
# ==================================================
def collect_sell_data(
    symbol: str,
    buy_price: float,
    sell_price: float,
    candles: List[Dict],
    holding_duration_minutes: int,
    pnl_ratio: float,
) -> str:
    """
    매도 시점 데이터 수집
    
    Args:
        symbol: 종목 코드
        buy_price: 매수 가격
        sell_price: 매도 가격
        candles: 매도 시점의 캔들 리스트
        holding_duration_minutes: 보유 기간 (분)
        pnl_ratio: 손익률
    
    Returns:
        str: 저장된 파일 경로
    """
    os.makedirs(SELL_DATA_DIR, exist_ok=True)
    
    # Feature 추출
    features = extract_all_features(
        candles,
        lookback=60,
        include_technical=True,
        include_patterns=True,
        include_volume=True,
    )
    
    # 데이터 구조
    data = {
        "symbol": symbol,
        "timestamp": datetime.now().isoformat(),
        "buy_price": buy_price,
        "sell_price": sell_price,
        "holding_duration_minutes": holding_duration_minutes,
        "pnl_ratio": pnl_ratio,
        "features": _serialize_features(features),
        "label": pnl_ratio > 0,  # 수익이면 True
    }
    
    # 파일 저장
    filename = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(SELL_DATA_DIR, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return filepath


# ==================================================
# 라벨 업데이트 (매수 데이터의 결과 업데이트)
# ==================================================
def update_buy_data_label(
    filepath: str,
    outcome: Dict,  # {"sell_price": float, "pnl_ratio": float, "holding_duration": int}
):
    """
    매수 데이터의 라벨 업데이트 (매도 후 호출)
    
    Args:
        filepath: 매수 데이터 파일 경로
        outcome: 매도 결과 정보
    """
    if not os.path.exists(filepath):
        return
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        data["label"] = outcome["pnl_ratio"] > 0
        data["outcome"] = outcome
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[update_buy_data_label] 업데이트 실패: {e}")


# ==================================================
# 유틸리티 함수
# ==================================================
def _serialize_features(features: Dict) -> Dict:
    """Feature를 JSON 직렬화 가능한 형태로 변환"""
    serialized = {}
    
    for key, value in features.items():
        if isinstance(value, np.ndarray):
            serialized[key] = value.tolist()
        elif isinstance(value, (int, float, bool, str)):
            serialized[key] = value
        elif isinstance(value, dict):
            serialized[key] = {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in value.items()}
        else:
            serialized[key] = str(value)
    
    return serialized


# numpy import (feature_engineer에서 사용)
import numpy as np







