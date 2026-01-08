# 딥러닝 Feature 설계 초안

## 📋 개요

현재 주식 자동매매 시스템에 딥러닝 기능을 통합하는 설계 초안입니다.
기존 구조를 유지하면서 딥러닝 모듈을 추가하는 방식으로 설계되었습니다.

## 🏗️ 구조

```
live/ml/
├── __init__.py              # 모듈 초기화
├── feature_engineer.py      # Feature 추출 및 전처리
├── model_manager.py         # 모델 관리 (로드/저장/추론)
├── ml_signals.py            # 딥러닝 기반 매매 신호 생성
├── data_collector.py        # 학습 데이터 수집
└── README.md               # 이 문서
```

## 📦 주요 모듈

### 1. feature_engineer.py
**역할**: OHLCV 데이터로부터 딥러닝 입력 feature 추출

**주요 기능**:
- 기본 OHLCV 시계열 feature (60개 캔들)
- 기술적 지표 (RSI, MACD, 볼린저 밴드)
- 캔들 패턴 feature (몸통 비율, 꼬리 비율, 장악형 등)
- 거래량 feature (거래량 비율, 추세 등)
- Feature 정규화 (Min-Max, Z-score)

**사용 예시**:
```python
from ml.feature_engineer import extract_all_features

features = extract_all_features(
    candles=candles,
    lookback=60,
    include_technical=True,
    include_patterns=True,
    include_volume=True,
)
```

### 2. model_manager.py
**역할**: 딥러닝 모델 통합 관리

**주요 클래스**:
- `BuySignalModel`: 매수 신호 예측 모델
- `SellSignalModel`: 매도 신호 예측 모델
- `StockScoringModel`: 종목 우선순위 스코어링 모델
- `ModelManager`: 모든 모델 통합 관리

**지원 프레임워크**:
- PyTorch (우선)
- TensorFlow (대안)

**사용 예시**:
```python
from ml.model_manager import ModelManager

model_mgr = ModelManager()
ml_prob, confidence = model_mgr.get_buy_signal(features)
```

### 3. ml_signals.py
**역할**: 딥러닝 기반 매매 신호 생성 (기존 strategy_signals.py와 통합)

**주요 기능**:
- 딥러닝 기반 매수 신호 생성
- 딥러닝 기반 매도 신호 생성
- 종목 우선순위 스코어링
- 하이브리드 접근 (규칙 기반 + 딥러닝)

**사용 예시**:
```python
from ml.ml_signals import get_hybrid_buy_signal

signal, details = get_hybrid_buy_signal(
    candles=candles,
    box_high=box_high,
    box_low=box_low,
    avg_volume=avg_volume,
    ml_weight=0.6,
    rule_weight=0.4,
    threshold=0.6,
)
```

### 4. data_collector.py
**역할**: 학습용 데이터 수집 및 저장

**주요 기능**:
- 매수 시점 데이터 수집
- 매도 시점 데이터 수집
- 라벨 업데이트 (매도 후 결과 반영)

**데이터 저장 위치**:
- `ml_data/buy/`: 매수 데이터
- `ml_data/sell/`: 매도 데이터
- `ml_data/scoring/`: 스코어링 데이터

## 🔄 기존 시스템과의 통합

### 1. check_n_buy.py 통합
```python
# check_n_buy.py 수정 예시
from ml.ml_signals import get_hybrid_buy_signal

def chk_n_buy(stk_cd: str, token: str, account_state):
    # ... 기존 로직 ...
    
    # 딥러닝 신호 확인
    candles = get_recent_candles(stk_cd)  # 캔들 조회 필요
    signal, details = get_hybrid_buy_signal(
        candles=candles,
        box_high=box_high,
        box_low=box_low,
        avg_volume=avg_volume,
    )
    
    if not signal:
        return
    
    # ... 매수 실행 ...
    
    # 데이터 수집
    from ml.data_collector import collect_buy_data
    collect_buy_data(
        symbol=stk_cd,
        candles=candles,
        box_high=box_high,
        box_low=box_low,
        avg_volume=avg_volume,
        buy_price=buy_price,
        buy_time=datetime.now(),
    )
```

### 2. check_n_sell.py 통합
```python
# check_n_sell.py 수정 예시
from ml.ml_signals import get_ml_sell_signal

def chk_n_sell(stk_cd: str, token: str, account_state, force: bool = False):
    # ... 기존 로직 ...
    
    # 딥러닝 매도 신호 확인
    candles = get_recent_candles(stk_cd)
    buy_price = account_state.holdings[stk_cd]["avg_price"]
    
    sell_signal = get_ml_sell_signal(
        buy_price=buy_price,
        current_price=current_price,
        candles=candles,
        holding_duration_minutes=holding_duration,
    )
    
    if sell_signal["final_signal"]:
        # 매도 실행
        # ...
```

### 3. strategy_state.py 확장
```python
# strategy_state.py에 딥러닝 관련 필드 추가
def _empty_state():
    return {
        # ... 기존 필드 ...
        
        # ===== 딥러닝 =====
        "ml_buy_prob": None,
        "ml_buy_confidence": None,
        "ml_sell_prob": None,
        "ml_sell_confidence": None,
        "ml_stock_score": None,
    }
```

## 📊 데이터 흐름

```
1. 실시간 거래
   ↓
2. 캔들 데이터 수집 (market/price_provider.py)
   ↓
3. Feature 추출 (ml/feature_engineer.py)
   ↓
4. 모델 추론 (ml/model_manager.py)
   ↓
5. 신호 생성 (ml/ml_signals.py)
   ↓
6. 매매 실행 (check_n_buy.py, check_n_sell.py)
   ↓
7. 데이터 수집 (ml/data_collector.py)
   ↓
8. 주기적 모델 재학습
```

## 🎯 구현 단계

### Phase 1: 기본 구조 구축 ✅
- [x] Feature 추출 모듈
- [x] 모델 관리 모듈
- [x] 신호 생성 모듈
- [x] 데이터 수집 모듈

### Phase 2: 기존 시스템 통합
- [ ] check_n_buy.py에 딥러닝 신호 통합
- [ ] check_n_sell.py에 딥러닝 신호 통합
- [ ] 캔들 데이터 조회 기능 추가
- [ ] strategy_state.py 확장

### Phase 3: 모델 개발
- [ ] 학습 데이터셋 구축
- [ ] 모델 아키텍처 설계 (LSTM, Transformer 등)
- [ ] 모델 학습 파이프라인
- [ ] 모델 평가 및 검증

### Phase 4: 실전 배포
- [ ] 모델 배포 및 모니터링
- [ ] A/B 테스트 (규칙 기반 vs 딥러닝)
- [ ] 성능 최적화

## 📝 주의사항

1. **의존성**: pandas, numpy 필요 (PyTorch/TensorFlow는 선택)
2. **캔들 데이터**: 현재 시스템에 캔들 조회 기능이 필요함
3. **모델 파일**: 초기에는 모델이 없을 수 있음 (기본값 반환)
4. **하이브리드 모드**: 초기에는 규칙 기반과 딥러닝을 병행 사용 권장

## 🔧 설정

### config.py에 추가할 설정
```python
# 딥러닝 설정
ML_ENABLED = True
ML_HYBRID_MODE = True
ML_BUY_THRESHOLD = 0.6
ML_SELL_THRESHOLD = 0.6
ML_WEIGHT = 0.6  # 딥러닝 가중치
RULE_WEIGHT = 0.4  # 규칙 기반 가중치
```

## 📚 참고

- 기존 `strategy_signals.py`와 병행 사용
- 모델이 없어도 기존 로직으로 동작 가능
- 점진적 통합 권장



