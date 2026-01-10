# 대기실장봇 (Waiting Room Manager Bot) v1

## 개요

대기실장봇은 장 마감 후 실행되어, 전 종목 중에서 가볍고 넓은 기준을 사용해 **'관찰 후보 종목 풀'**을 구성하는 배치 시스템입니다.

**핵심 역할**: 정밀 분석 이전 단계에서 종목을 '대기실에 올려놓는 역할'만 수행

## 파이프라인 위치

```
(외부 트리거) 장 마감 후 실행
    ↓
대기실장봇: 후보풀 생성 (candidate_pool_YYYYMMDD.json)
    ↓
캔들기록봇: 후보 종목 OHLCV 수집/저장 (ohlcv_YYYYMMDD.csv)
    ↓
문지기봇: 1·2·3차 필터/점수 계산으로 최종 watchlist 생성
    ↓
정찰봇: 장중 감시
```

## 실행 방법

### 기본 실행
```bash
cd scout_selector
python build_candidate_pool.py
```

### 옵션
```bash
# 특정 날짜 지정
python build_candidate_pool.py --date 20260107

# 기존 파일이 있어도 재생성
python build_candidate_pool.py --force

# 최대 종목 수 제한
python build_candidate_pool.py --max-symbols 800

# 조합 사용
python build_candidate_pool.py --date 20260107 --force --max-symbols 500
```

### Windows 배치 스크립트
```bash
scripts\run\run_candidate_pool.bat
```

## 입력 소스

대기실장봇은 다음 입력 소스를 병합합니다:

1. **거래대금 상위 N** (기본: 300개)
   - 추후 API/파일 연동 확장 가능
   
2. **거래량 상위/급증 N** (기본: 200개)
   - 추후 API/파일 연동 확장 가능
   
3. **조건식/시그널 결과**
   - `input/conditions/conditions_YYYYMMDD.json`에서 읽기
   - `signals_collector` 모듈에서 생성된 파일 사용
   
4. **고정 기준 종목** (항상 포함)
   - `005930` (삼성전자)
   - `000660` (SK하이닉스)

## 출력 형식

### 파일 경로
```
scout_selector/output/candidate_pool_YYYYMMDD.json
```

### JSON 스키마
```json
{
  "meta": {
    "date": "20260107",
    "created_at": "2026-01-07T15:40:00+09:00",
    "bot_name": "대기실장봇",
    "bot_version": "1.0.0"
  },
  "sources": {
    "turnover_top": 300,
    "volume_top": 200,
    "conditions": 45,
    "fixed_symbols": 2
  },
  "symbols": [
    "005930",
    "000660",
    "123456"
  ]
}
```

## 오류 처리

- **입력 소스 일부 실패**: 해당 소스만 스킵하고 나머지로 후보 풀 생성
- **모든 소스 실패**: 고정 기준 종목만 포함한 최소 후보 풀 생성
- **예외 발생**: 에러 로그 출력 후 최소 후보 풀 생성 시도

## 멱등성 (Idempotency)

- 동일 날짜(YYYYMMDD) 출력 파일이 존재하면 기본적으로 재생성하지 않음
- `--force` 옵션으로 강제 재생성 가능

## 명시적 금지 사항

대기실장봇은 다음 작업을 **절대 수행하지 않습니다**:

- ❌ OHLCV 정밀 계산
- ❌ 추세/구조/패턴 분석
- ❌ 점수 계산
- ❌ 최종 종목 선정
- ❌ 매수·매도 판단
- ❌ 장중 데이터 사용

## 다음 단계

대기실장봇의 출력(`candidate_pool_YYYYMMDD.json`)은 **캔들기록봇**의 입력으로 사용됩니다.

캔들기록봇은 후보 풀에 포함된 종목만을 대상으로 OHLCV를 수집하여 `scout_selector/data/ohlcv_YYYYMMDD.csv`를 생성합니다.

---

**버전**: 1.0.0  
**최종 업데이트**: 2026-01-07






