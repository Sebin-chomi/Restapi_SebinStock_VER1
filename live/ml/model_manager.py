# ml/model_manager.py
"""
딥러닝 모델 관리 모듈

역할:
- 모델 로드/저장
- 모델 추론 (inference)
- 모델 버전 관리
- 모델 성능 모니터링
"""

from __future__ import annotations

import os
import pickle
from typing import Dict, Optional, Tuple
from datetime import datetime
import numpy as np

# PyTorch 또는 TensorFlow import (선택)
try:
    import torch
    import torch.nn as nn
    FRAMEWORK = "pytorch"
except ImportError:
    try:
        import tensorflow as tf
        FRAMEWORK = "tensorflow"
    except ImportError:
        FRAMEWORK = None


# ==================================================
# 모델 저장 경로 설정
# ==================================================
MODEL_DIR = "models"
BUY_MODEL_NAME = "buy_model"
SELL_MODEL_NAME = "sell_model"
SCORING_MODEL_NAME = "scoring_model"


# ==================================================
# 모델 인터페이스 (추상 클래스)
# ==================================================
class BaseModel:
    """모든 딥러닝 모델의 기본 클래스"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.model = None
        self.is_loaded = False
    
    def load(self, model_path: Optional[str] = None):
        """모델 로드"""
        raise NotImplementedError
    
    def predict(self, features: Dict) -> float:
        """추론 수행"""
        raise NotImplementedError
    
    def save(self, save_path: str):
        """모델 저장"""
        raise NotImplementedError


# ==================================================
# 매수 신호 모델
# ==================================================
class BuySignalModel(BaseModel):
    """
    매수 신호 예측 모델
    
    입력:
        - OHLCV 시계열 (60개 캔들)
        - 기술적 지표 (RSI, MACD, 볼린저 밴드 등)
        - 캔들 패턴 feature
        - 거래량 feature
    
    출력:
        - 매수 신호 확률 (0.0 ~ 1.0)
        - 신뢰도 점수
    """
    
    def __init__(self, model_path: Optional[str] = None):
        super().__init__(model_path)
        self.model = None
        self.scaler = None  # Feature 정규화용
    
    def load(self, model_path: Optional[str] = None):
        """모델 로드"""
        if model_path:
            self.model_path = model_path
        
        if not self.model_path or not os.path.exists(self.model_path):
            # 모델이 없으면 기본값 반환하도록 설정
            self.is_loaded = False
            return
        
        try:
            if FRAMEWORK == "pytorch":
                self.model = torch.load(self.model_path, map_location="cpu")
                self.model.eval()
            elif FRAMEWORK == "tensorflow":
                self.model = tf.keras.models.load_model(self.model_path)
            
            # Scaler 로드 (있는 경우)
            scaler_path = self.model_path.replace(".pth", "_scaler.pkl").replace(".h5", "_scaler.pkl")
            if os.path.exists(scaler_path):
                with open(scaler_path, "rb") as f:
                    self.scaler = pickle.load(f)
            
            self.is_loaded = True
        except Exception as e:
            print(f"[BuySignalModel] 모델 로드 실패: {e}")
            self.is_loaded = False
    
    def predict(self, features: Dict) -> Tuple[float, float]:
        """
        매수 신호 예측
        
        Args:
            features: feature_engineer에서 추출한 feature 딕셔너리
        
        Returns:
            tuple: (매수 확률, 신뢰도 점수)
        """
        if not self.is_loaded or self.model is None:
            # 모델이 없으면 기본값 반환 (기존 로직 사용)
            return 0.0, 0.0
        
        try:
            # Feature 전처리
            processed_features = self._preprocess_features(features)
            
            # 추론
            if FRAMEWORK == "pytorch":
                with torch.no_grad():
                    output = self.model(processed_features)
                    if isinstance(output, torch.Tensor):
                        prob = float(output.item())
                    else:
                        prob = float(output)
            elif FRAMEWORK == "tensorflow":
                output = self.model.predict(processed_features, verbose=0)
                prob = float(output[0][0]) if len(output.shape) > 1 else float(output[0])
            
            # 신뢰도 계산 (확률이 0.5에 가까우면 낮은 신뢰도)
            confidence = abs(prob - 0.5) * 2.0  # 0.0 ~ 1.0
            
            return prob, confidence
        
        except Exception as e:
            print(f"[BuySignalModel] 예측 실패: {e}")
            return 0.0, 0.0
    
    def _preprocess_features(self, features: Dict) -> np.ndarray:
        """Feature 전처리 (모델 입력 형태로 변환)"""
        # 실제 구현은 모델 구조에 따라 달라짐
        # 예시: OHLCV 시계열 + 기술적 지표를 하나의 벡터로 결합
        ohlcv = features.get("ohlcv_sequence", np.zeros((60, 5)))
        
        # Flatten 또는 모델에 맞는 형태로 변환
        # 여기서는 간단히 flatten (실제로는 모델 구조에 맞게)
        feature_vector = ohlcv.flatten()
        
        # 기술적 지표 추가
        tech_features = [
            features.get("rsi", 50.0) / 100.0,  # 정규화
            features.get("macd", 0.0),
            features.get("macd_histogram", 0.0),
            features.get("bb_bandwidth", 0.0),
        ]
        
        feature_vector = np.concatenate([feature_vector, tech_features])
        
        # 정규화 (scaler가 있으면 사용)
        if self.scaler:
            feature_vector = self.scaler.transform(feature_vector.reshape(1, -1))
            feature_vector = feature_vector.flatten()
        
        return feature_vector.reshape(1, -1)  # 배치 차원 추가
    
    def save(self, save_path: str):
        """모델 저장"""
        if not self.model:
            return
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        try:
            if FRAMEWORK == "pytorch":
                torch.save(self.model, save_path)
            elif FRAMEWORK == "tensorflow":
                self.model.save(save_path)
            
            # Scaler 저장
            if self.scaler:
                scaler_path = save_path.replace(".pth", "_scaler.pkl").replace(".h5", "_scaler.pkl")
                with open(scaler_path, "wb") as f:
                    pickle.dump(self.scaler, f)
        except Exception as e:
            print(f"[BuySignalModel] 모델 저장 실패: {e}")


# ==================================================
# 매도 신호 모델
# ==================================================
class SellSignalModel(BaseModel):
    """
    매도 신호 예측 모델
    
    입력:
        - 보유 종목의 현재 상태
        - 매수 이후 가격 변화
        - 기술적 지표
        - 손익률
    
    출력:
        - 매도 신호 확률 (0.0 ~ 1.0)
    """
    
    def __init__(self, model_path: Optional[str] = None):
        super().__init__(model_path)
        self.model = None
    
    def load(self, model_path: Optional[str] = None):
        """모델 로드"""
        if model_path:
            self.model_path = model_path
        
        if not self.model_path or not os.path.exists(self.model_path):
            self.is_loaded = False
            return
        
        try:
            if FRAMEWORK == "pytorch":
                self.model = torch.load(self.model_path, map_location="cpu")
                self.model.eval()
            elif FRAMEWORK == "tensorflow":
                self.model = tf.keras.models.load_model(self.model_path)
            
            self.is_loaded = True
        except Exception as e:
            print(f"[SellSignalModel] 모델 로드 실패: {e}")
            self.is_loaded = False
    
    def predict(
        self,
        buy_price: float,
        current_price: float,
        features: Dict,
        holding_duration_minutes: int = 0,
    ) -> Tuple[float, float]:
        """
        매도 신호 예측
        
        Args:
            buy_price: 매수 가격
            current_price: 현재 가격
            features: 현재 시점의 feature
            holding_duration_minutes: 보유 기간 (분)
        
        Returns:
            tuple: (매도 확률, 신뢰도 점수)
        """
        if not self.is_loaded or self.model is None:
            return 0.0, 0.0
        
        try:
            # 손익률 계산
            pnl_ratio = (current_price - buy_price) / buy_price if buy_price > 0 else 0.0
            
            # Feature 전처리
            processed_features = self._preprocess_features(
                features, pnl_ratio, holding_duration_minutes
            )
            
            # 추론
            if FRAMEWORK == "pytorch":
                with torch.no_grad():
                    output = self.model(processed_features)
                    prob = float(output.item()) if isinstance(output, torch.Tensor) else float(output)
            elif FRAMEWORK == "tensorflow":
                output = self.model.predict(processed_features, verbose=0)
                prob = float(output[0][0]) if len(output.shape) > 1 else float(output[0])
            
            confidence = abs(prob - 0.5) * 2.0
            
            return prob, confidence
        
        except Exception as e:
            print(f"[SellSignalModel] 예측 실패: {e}")
            return 0.0, 0.0
    
    def _preprocess_features(
        self, features: Dict, pnl_ratio: float, holding_duration: int
    ) -> np.ndarray:
        """Feature 전처리"""
        # 손익률, 보유 기간 등을 feature에 추가
        feature_vector = np.array([
            pnl_ratio,
            holding_duration / 1000.0,  # 정규화 (대략 1일 = 1440분)
            features.get("rsi", 50.0) / 100.0,
            features.get("macd_histogram", 0.0),
        ])
        
        return feature_vector.reshape(1, -1)
    
    def save(self, save_path: str):
        """모델 저장"""
        if not self.model:
            return
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        try:
            if FRAMEWORK == "pytorch":
                torch.save(self.model, save_path)
            elif FRAMEWORK == "tensorflow":
                self.model.save(save_path)
        except Exception as e:
            print(f"[SellSignalModel] 모델 저장 실패: {e}")


# ==================================================
# 종목 스코어링 모델
# ==================================================
class StockScoringModel(BaseModel):
    """
    종목 우선순위 스코어링 모델
    
    입력:
        - 종목의 feature
        - 시장 상황
    
    출력:
        - 종목 점수 (0.0 ~ 1.0) - 높을수록 우선순위 높음
    """
    
    def __init__(self, model_path: Optional[str] = None):
        super().__init__(model_path)
        self.model = None
    
    def load(self, model_path: Optional[str] = None):
        """모델 로드"""
        if model_path:
            self.model_path = model_path
        
        if not self.model_path or not os.path.exists(self.model_path):
            self.is_loaded = False
            return
        
        try:
            if FRAMEWORK == "pytorch":
                self.model = torch.load(self.model_path, map_location="cpu")
                self.model.eval()
            elif FRAMEWORK == "tensorflow":
                self.model = tf.keras.models.load_model(self.model_path)
            
            self.is_loaded = True
        except Exception as e:
            print(f"[StockScoringModel] 모델 로드 실패: {e}")
            self.is_loaded = False
    
    def predict(self, features: Dict) -> float:
        """
        종목 점수 예측
        
        Args:
            features: 종목의 feature
        
        Returns:
            float: 종목 점수 (0.0 ~ 1.0)
        """
        if not self.is_loaded or self.model is None:
            return 0.5  # 기본값
        
        try:
            processed_features = self._preprocess_features(features)
            
            if FRAMEWORK == "pytorch":
                with torch.no_grad():
                    output = self.model(processed_features)
                    score = float(output.item()) if isinstance(output, torch.Tensor) else float(output)
            elif FRAMEWORK == "tensorflow":
                output = self.model.predict(processed_features, verbose=0)
                score = float(output[0][0]) if len(output.shape) > 1 else float(output[0])
            
            return max(0.0, min(1.0, score))  # 0~1 범위로 클리핑
        
        except Exception as e:
            print(f"[StockScoringModel] 예측 실패: {e}")
            return 0.5
    
    def _preprocess_features(self, features: Dict) -> np.ndarray:
        """Feature 전처리"""
        # 주요 feature만 선택
        feature_vector = np.array([
            features.get("rsi", 50.0) / 100.0,
            features.get("macd_histogram", 0.0),
            features.get("volume_ma_ratio", 1.0),
            features.get("bb_bandwidth", 0.0),
        ])
        
        return feature_vector.reshape(1, -1)
    
    def save(self, save_path: str):
        """모델 저장"""
        if not self.model:
            return
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        try:
            if FRAMEWORK == "pytorch":
                torch.save(self.model, save_path)
            elif FRAMEWORK == "tensorflow":
                self.model.save(save_path)
        except Exception as e:
            print(f"[StockScoringModel] 모델 저장 실패: {e}")


# ==================================================
# 모델 매니저 (통합 관리)
# ==================================================
class ModelManager:
    """모든 모델을 통합 관리하는 클래스"""
    
    def __init__(self, model_dir: str = MODEL_DIR):
        self.model_dir = model_dir
        self.buy_model = BuySignalModel()
        self.sell_model = SellSignalModel()
        self.scoring_model = StockScoringModel()
        
        # 모델 로드
        self._load_all_models()
    
    def _load_all_models(self):
        """모든 모델 로드"""
        buy_path = os.path.join(self.model_dir, f"{BUY_MODEL_NAME}.pth")
        sell_path = os.path.join(self.model_dir, f"{SELL_MODEL_NAME}.pth")
        scoring_path = os.path.join(self.model_dir, f"{SCORING_MODEL_NAME}.pth")
        
        self.buy_model.load(buy_path)
        self.sell_model.load(sell_path)
        self.scoring_model.load(scoring_path)
    
    def reload_models(self):
        """모든 모델 재로드"""
        self._load_all_models()
    
    def get_buy_signal(self, features: Dict) -> Tuple[float, float]:
        """매수 신호 조회"""
        return self.buy_model.predict(features)
    
    def get_sell_signal(
        self,
        buy_price: float,
        current_price: float,
        features: Dict,
        holding_duration_minutes: int = 0,
    ) -> Tuple[float, float]:
        """매도 신호 조회"""
        return self.sell_model.predict(buy_price, current_price, features, holding_duration_minutes)
    
    def get_stock_score(self, features: Dict) -> float:
        """종목 점수 조회"""
        return self.scoring_model.predict(features)










