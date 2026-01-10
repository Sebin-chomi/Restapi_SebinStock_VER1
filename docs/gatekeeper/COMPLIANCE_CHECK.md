# 문지기봇 구현 완료 기준 검증

## ✅ 출력 데이터 계약 준수

### 필수 필드 확인

| 필드 | 상태 | 위치 |
|------|------|------|
| 종목코드 | ✅ | `symbol` |
| 카테고리 | ✅ | `category` (및 `bucket` 호환성 유지) |
| 선정 사유 요약 | ✅ | `reason.summary` |
| 구조 점수 (해당 시) | ✅ | `structure_score` (구조형만) |
| 사용된 주요 지표 값 | ✅ | `indicators` |
| 생성 일시 | ✅ | `meta.created_at` |
| 문지기봇 버전 | ✅ | `meta.gatekeeper_bot_version` |

### 출력 형식

```json
{
  "meta": {
    "date": "20260107",
    "created_at": "2026-01-07T15:35:00.123456",
    "phase": "normal",
    "gatekeeper_bot_version": "1.0.0"
  },
  "largecap": [...],
  "volume": [...],
  "structure": [...],
  "theme": [...]
}
```

각 종목 항목:
```json
{
  "symbol": "035420",
  "category": "volume",
  "bucket": "volume",
  "score": 0.85,
  "structure_score": 72.0,  // 구조형만
  "reason": {
    "summary": "거래량형 선정 (거래대금: 5,000,000,000원, ...)",
    ...
  },
  "indicators": {
    ...
  }
}
```

## ✅ 명시적 금지 사항 준수

### 1. 매수/매도 판단
- ✅ **준수**: 종목 선정만 수행, 매수/매도 타이밍 판단 없음
- ✅ 코드 검증: `selector.py`에 매수/매도 관련 로직 없음

### 2. 장 중 재선정
- ✅ **준수**: 장 마감 후 1일 1회 실행 (배치 프로세스)
- ✅ 실행 스크립트: `runner.py`, `prepare_tomorrow.py` (수동 실행 또는 스케줄러)

### 3. 실시간 데이터 의존
- ✅ **준수**: 일봉 OHLCV만 사용
- ✅ 코드 검증: `compute_features()`는 일봉 데이터만 사용
- ✅ 실시간 체결/호가 데이터 사용 없음

### 4. 계좌/주문 API 접근
- ✅ **준수**: 계좌 조회, 주문 API 호출 없음
- ✅ 코드 검증: `selector.py`에 API 호출 없음
- ✅ 독립 모듈: `scout_selector`는 다른 모듈 import 없음 (theme_score_builder 제외)

## ✅ 구현 완료 기준 검증

### 1. 동일 입력 → 동일 출력 보장

**확인 사항:**
- ✅ 랜덤 요소 없음 (`random`, `shuffle` 등 사용 안 함)
- ✅ 시간 의존성 없음 (생성 일시 제외, 알고리즘은 시간 무관)
- ✅ 외부 API 호출 없음 (입력 파일만 사용)
- ✅ 결정론적 알고리즘 사용 (pandas 정렬, 점수 계산 등)

**검증 방법:**
```python
# 동일 입력으로 2회 실행 시 동일 출력 확인
result1 = select_watchlist(df, cfg=cfg, ...)
result2 = select_watchlist(df, cfg=cfg, ...)
assert result1 == result2  # True여야 함
```

### 2. 왜 이 종목이 선택되었는지 설명 가능

**확인 사항:**
- ✅ `reason.summary`: 사람이 읽기 쉬운 선정 사유 요약
- ✅ `reason`: 상세 선정 사유 (카테고리별 상이)
- ✅ `indicators`: 사용된 주요 지표 값
- ✅ `structure_score`: 구조형의 경우 구조 점수 명시

**예시:**
```json
{
  "reason": {
    "summary": "구조형 선정 (점수: 72점, MA 정배열, MA 상향 돌파, Higher Low)",
    "structure_score": 72.0,
    "ma_aligned": true,
    "ma_breakout": true,
    ...
  },
  "indicators": {
    "structure_score": 72.0,
    "ma5": 45000.0,
    "ma20": 44000.0,
    ...
  }
}
```

### 3. 정찰봇과 역할 충돌 없음

**역할 분리:**
- ✅ **문지기봇**: 종목 선정만 담당 (배치 프로세스, 장 마감 후 실행)
- ✅ **정찰봇**: 선정된 종목 감시 및 기록 (상시 프로세스, 장 중 실행)
- ✅ **역할 분리 명확**: 문지기봇은 정찰봇의 입력만 생성

**데이터 흐름:**
```
문지기봇 (장 마감 후)
  ↓
watchlist_YYYYMMDD.json 생성 (불변 스냅샷)
  ↓
정찰봇 (다음 거래일 장 중)
  ↓
watchlist_YYYYMMDD.json 읽기
  ↓
선정된 종목 감시 및 기록
```

**충돌 없음 확인:**
- ✅ 문지기봇은 watchlist 생성만 수행
- ✅ 정찰봇은 watchlist 읽기만 수행
- ✅ 정찰봇은 watchlist 수정하지 않음
- ✅ 문지기봇은 정찰봇 실행 중 재실행하지 않음

## 📋 검증 체크리스트

- [x] 출력 데이터 계약 준수 (모든 필수 필드 포함)
- [x] 명시적 금지 사항 준수 (매수/매도 판단, 장 중 재선정, 실시간 데이터, 계좌/주문 API 접근 금지)
- [x] 동일 입력 → 동일 출력 보장 (결정론적 알고리즘)
- [x] 선정 사유 설명 가능 (reason.summary, reason, indicators)
- [x] 정찰봇과 역할 충돌 없음 (역할 분리 명확)

## 🎯 최종 확인

모든 구현 완료 기준을 충족했습니다.

- ✅ 출력은 불변 스냅샷으로 생성
- ✅ 모든 필수 필드 포함
- ✅ 명시적 금지 사항 준수
- ✅ 동일 입력 → 동일 출력 보장
- ✅ 선정 사유 설명 가능
- ✅ 정찰봇과 역할 충돌 없음







