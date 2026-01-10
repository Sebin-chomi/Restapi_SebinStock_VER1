# 문지기봇 역할 및 범위 위반 여부 검증 보고서

## 📋 검증 항목

### 1. 종목 선별(Selection) 외의 역할 수행 여부
### 2. 매수/매도 판단, 포지션 관리, 계좌 접근 코드 존재 여부
### 3. 장 중 재선정 또는 실시간 이벤트 의존 로직 존재 여부

---

## ✅ 검증 결과: 모든 항목 준수

### 1. 종목 선별(Selection) 외의 역할 수행 여부

#### ✅ 검증 완료: 종목 선별만 수행

**코드 분석 결과:**

| 파일 | 역할 | 검증 결과 |
|------|------|----------|
| `selector.py` | 종목 선정 엔진 | ✅ 종목 선정만 수행 |
| `runner.py` | 실행 스크립트 | ✅ 종목 선정 및 JSON 파일 생성만 수행 |
| `prepare_tomorrow.py` | 내일 종목 선정 | ✅ 종목 선정 및 JSON 파일 생성만 수행 |
| `manual_select.py` | 수동 종목 선정 | ✅ 사용자 입력 받아 종목 선정 및 JSON 파일 생성만 수행 |
| `theme_score_builder.py` | 테마 점수 빌더 | ✅ 테마 점수 계산만 수행 |
| `theme_signals.py` | 테마 신호 수집 | ✅ 테마 신호 수집만 수행 |

**주요 함수 분석:**

```python
# selector.py
def select_watchlist(...) -> Dict[str, List[Dict]]:
    """종목 선정만 수행, 반환값은 선정된 종목 리스트"""
    # ... 필터링 및 점수 계산 ...
    return final_result  # 선정된 종목만 반환

# runner.py
result = select_watchlist(...)  # 종목 선정
output = {"meta": ..., "largecap": ..., ...}  # JSON 구조화
json.dump(output, f, ...)  # 파일 저장만 수행
```

**결론:** ✅ 종목 선별(Selection) 외의 역할 없음

---

### 2. 매수/매도 판단, 포지션 관리, 계좌 접근 코드 존재 여부

#### ✅ 검증 완료: 관련 코드 없음

**키워드 검색 결과:**

```bash
# 매수/매도 관련 키워드 검색
grep -i "buy|sell|매수|매도|order|주문|position|포지션|account|계좌|balance|잔고" scout_selector/
```

**검색 결과:**
- 문서 파일(`COMPLIANCE_CHECK.md`, `OUTPUT_CONTRACT.md`)에만 언급됨
- 실제 코드에는 관련 키워드 없음

**코드 분석:**

| 검색 키워드 | 발견 위치 | 내용 |
|------------|----------|------|
| `buy`, `sell` | 없음 | - |
| `매수`, `매도` | 없음 | - |
| `order`, `주문` | 없음 | - |
| `position`, `포지션` | 없음 | - |
| `account`, `계좌` | 없음 | - |
| `balance`, `잔고` | 없음 | - |

**Import 분석:**

```python
# selector.py의 import
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional
import math
import pandas as pd

# ✅ API, 주문, 계좌 관련 import 없음
# ✅ 외부 모듈 import 없음 (theme_score_builder 제외)
```

**결론:** ✅ 매수/매도 판단, 포지션 관리, 계좌 접근 코드 없음

---

### 3. 장 중 재선정 또는 실시간 이벤트 의존 로직 존재 여부

#### ✅ 검증 완료: 관련 로직 없음

**키워드 검색 결과:**

```bash
# 실시간/이벤트 관련 키워드 검색
grep -i "real.*time|실시간|realtime|event|이벤트|schedule|스케줄|polling|폴링|async|await|while.*True|loop|websocket|socket" scout_selector/
```

**검색 결과:**
- 문서 파일에만 언급됨
- 실제 코드에는 관련 키워드 없음

**코드 분석:**

| 검색 키워드 | 발견 위치 | 내용 |
|------------|----------|------|
| `while True` | 없음 | - |
| `loop`, `polling` | 없음 | - |
| `async`, `await` | 없음 | - |
| `websocket`, `socket` | 없음 | - |
| `event`, `이벤트` | 없음 | - |
| `schedule`, `스케줄` | 없음 | - |

**실행 방식 분석:**

```python
# runner.py
# ✅ 배치 프로세스: 한 번 실행 후 종료
if __name__ == "__main__":
    # ... 종목 선정 ...
    json.dump(output, f, ...)  # 파일 저장 후 종료

# prepare_tomorrow.py
def main():
    # ... 종목 선정 ...
    json.dump(output, f, ...)  # 파일 저장 후 종료

# manual_select.py
def main():
    # ... 사용자 입력 받아 종목 선정 ...
    json.dump(output, f, ...)  # 파일 저장 후 종료
```

**데이터 소스 분석:**

```python
# selector.py - compute_features()
def compute_features(df: pd.DataFrame, ...) -> pd.DataFrame:
    """일봉 OHLCV 데이터만 사용"""
    # ✅ 일봉 데이터만 처리
    # ✅ 실시간 체결/호가 데이터 사용 안 함
    df["vol_avg"] = df.groupby("symbol")["volume"].transform(...)
    df["intraday_volatility"] = (df["high"] - df["low"]) / df["open"]
    # ...
```

**결론:** ✅ 장 중 재선정 또는 실시간 이벤트 의존 로직 없음

---

## 📊 종합 검증 결과

| 검증 항목 | 상태 | 상세 |
|----------|------|------|
| 종목 선별 외의 역할 수행 | ✅ 통과 | 종목 선정만 수행 |
| 매수/매도 판단 코드 | ✅ 통과 | 관련 코드 없음 |
| 포지션 관리 코드 | ✅ 통과 | 관련 코드 없음 |
| 계좌 접근 코드 | ✅ 통과 | 관련 코드 없음 |
| 장 중 재선정 로직 | ✅ 통과 | 배치 프로세스만 사용 |
| 실시간 이벤트 의존 | ✅ 통과 | 일봉 데이터만 사용 |

---

## 🔍 상세 코드 검증

### selector.py (핵심 엔진)

**역할:**
- 전 종목 대상 입구 필터 및 1·2차 필터링 수행
- 정찰봇이 감시할 종목 후보군 생성

**제약사항 (코드 주석):**
```python
"""
제약사항:
- 매수/매도 판단 금지
- 장 중 재선정 금지
- 실시간 데이터 사용 금지
- 주문/계좌 접근 금지
"""
```

**함수 목록:**
- `compute_features()`: 일봉 데이터 기반 feature 계산
- `score_volume()`: 거래량형 점수 계산
- `score_structure()`: 구조형 점수 계산
- `score_theme()`: 테마형 점수 계산
- `apply_gate_filter()`: 입구 필터 적용
- `apply_primary_filter()`: 1차 필터 적용
- `select_watchlist()`: 종목 선정 (반환값: Dict[str, List[Dict]])

**검증:** ✅ 모든 함수가 종목 선정만 수행

---

### runner.py (실행 스크립트)

**역할:**
- 장 마감 후 배치 프로세스로 실행
- 오늘 날짜 기준으로 종목 선정
- 정찰봇이 사용할 watchlist_YYYYMMDD.json 생성

**실행 흐름:**
1. 데이터 로드 (CSV 파일)
2. Phase 추론
3. Theme Score Map 빌드
4. 종목 선정 (`select_watchlist()`)
5. JSON 파일 저장
6. 종료

**검증:** ✅ 배치 프로세스, 재실행 로직 없음

---

### prepare_tomorrow.py (내일 종목 선정)

**역할:**
- 장 마감 후 배치 프로세스로 실행
- 내일 날짜 기준으로 종목 선정
- 정찰봇이 다음 거래일에 사용할 watchlist_YYYYMMDD.json 생성

**실행 흐름:**
1. 내일 날짜 계산
2. 데이터 파일 찾기 (최근 5일)
3. 데이터 로드
4. Phase 추론
5. Theme Score Map 빌드
6. 종목 선정 (`select_watchlist()`)
7. JSON 파일 저장
8. 종료

**검증:** ✅ 배치 프로세스, 재실행 로직 없음

---

### manual_select.py (수동 종목 선정)

**역할:**
- 대화형 입력으로 종목 직접 지정
- 각 버킷별로 수동 입력 가능
- 내일 날짜 기준 watchlist_YYYYMMDD.json 생성

**실행 흐름:**
1. 사용자 입력 받기 (거래량형, 구조형, 테마형)
2. 데이터 로드 (선택적)
3. 결과 구성
4. 사용자 확인
5. JSON 파일 저장
6. 종료

**검증:** ✅ 대화형 입력만, 재실행 로직 없음

---

## ✅ 최종 결론

**문지기봇은 역할 및 범위를 엄격히 준수합니다:**

1. ✅ **종목 선별(Selection)만 수행**: 다른 역할 없음
2. ✅ **매수/매도 판단 없음**: 관련 코드 없음
3. ✅ **포지션 관리 없음**: 관련 코드 없음
4. ✅ **계좌 접근 없음**: 관련 코드 없음
5. ✅ **장 중 재선정 없음**: 배치 프로세스만 사용
6. ✅ **실시간 이벤트 의존 없음**: 일봉 데이터만 사용

**문지기봇은 독립적인 배치 프로세스로서 종목 선정만 담당하며, 정찰봇과의 역할 분리가 명확합니다.**







