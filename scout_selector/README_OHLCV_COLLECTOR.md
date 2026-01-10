# 캔들기록봇 (OHLCV Collector) v1

## 개요

캔들기록봇은 장 마감 후 실행되어, 대기실장봇이 만든 후보 풀을 입력으로 받아 **일봉 OHLCV 데이터를 수집·기록**하는 배치 시스템입니다.

**핵심 역할**: 사실 기록만 수행 (Source of Truth)

## 파이프라인 위치

```
(외부 트리거) 장 마감 후 실행
    ↓
대기실장봇 → candidate_pool_YYYYMMDD.json
    ↓
캔들기록봇 → ohlcv_YYYYMMDD.csv
    ↓
문지기봇 → watchlist_YYYYMMDD.json
    ↓
정찰봇: 장중 감시
```

## 실행 방법

### 기본 실행
```bash
cd scout_selector
python collect_ohlcv.py
```

### 옵션
```bash
# 특정 날짜 지정
python collect_ohlcv.py --date 20260107

# 기존 파일이 있어도 재생성
python collect_ohlcv.py --force

# 수동 종목 리스트 파일 지정 (Cold Start 보조 입력)
python collect_ohlcv.py --symbols-file symbols.txt

# 조합 사용
python collect_ohlcv.py --date 20260107 --force
```

### Windows 배치 스크립트
```bash
scripts\run\run_ohlcv_collector.bat
```

## 입력 소스

캔들기록봇은 다음 입력 소스를 병합합니다:

1. **대기실장봇 출력** (우선)
   - `scout_selector/output/candidate_pool_YYYYMMDD.json`
   - 필수 필드: `symbols: [string]`

2. **수동 종목 리스트** (옵션)
   - `--symbols-file` 옵션으로 지정
   - 한 줄에 하나씩 종목 코드

3. **고정 기준 종목** (항상 포함)
   - `005930` (삼성전자)
   - `000660` (SK하이닉스)

## 출력 형식

### 파일 경로
```
scout_selector/data/ohlcv_YYYYMMDD.csv
```

### CSV 스키마
```csv
date,symbol,open,high,low,close,volume,turnover_krw
2026-01-07,005930,75000,76000,74500,75500,1000000,75500000000
2026-01-07,000660,120000,125000,119000,123000,500000,61500000000
```

**컬럼 설명**:
- `date`: 날짜 (YYYY-MM-DD)
- `symbol`: 종목 코드
- `open`: 시가 (원)
- `high`: 고가 (원)
- `low`: 저가 (원)
- `close`: 종가 (원)
- `volume`: 거래량 (주식 수)
- `turnover_krw`: 거래대금 (원, 종가 × 거래량)

## 데이터 수집 방식

현재는 **pykrx** 라이브러리를 사용하여 일봉 OHLCV 데이터를 수집합니다.

```python
from pykrx import stock
df = stock.get_market_ohlcv_by_date(date, date, symbol)
```

**필요 패키지**:
```bash
pip install pykrx
```

## 오류 처리

- **종목별 수집 실패**: 해당 종목만 스킵하고 나머지 계속 수집
- **모든 종목 실패**: 고정 기준 종목만 수집 시도
- **완전 실패**: 빈 CSV라도 생성 (헤더만 포함)
- **예외 발생**: 상세 로그 출력 후 최소 CSV 생성 시도

## Cold Start 처리

입력 종목이 전혀 없는 경우:
- 고정 기준 종목만 수집

데이터 소스 장애 시:
- 가능한 종목만 수집 후 종료

결과:
- CSV는 항상 생성 시도 (최소 행이라도)

## 멱등성 (Idempotency)

- 동일 날짜(YYYYMMDD) 출력 파일이 존재하면 기본적으로 재생성하지 않음
- `--force` 옵션으로 강제 재생성 가능

## 명시적 금지 사항

캔들기록봇은 다음 작업을 **절대 수행하지 않습니다**:

- ❌ 종목 선정/점수 계산/분석(추세·구조)
- ❌ 매수·매도 판단
- ❌ 주문/계좌 접근
- ❌ 장중 재선정/실시간 이벤트 의존

## 문지기봇 연계 계약

문지기봇은 **ohlcv_YYYYMMDD.csv**를 입력으로 사용합니다.

**날짜 일치 규칙**:
- 문지기봇 실행 날짜와 CSV 날짜가 일치해야 함
- 예: `prepare_tomorrow.py` 실행 시 내일 날짜의 CSV를 찾음

캔들기록봇은 문지기봇 로직을 알 필요 없습니다.

## 다음 단계

캔들기록봇의 출력(`ohlcv_YYYYMMDD.csv`)은 **문지기봇**의 입력으로 사용됩니다.

문지기봇은 OHLCV 데이터를 기반으로 필터링 및 점수 계산을 수행하여 최종 watchlist를 생성합니다.

---

**버전**: 1.0.0  
**최종 업데이트**: 2026-01-07






