# Post-Market 파이프라인 자동화

## 개요

장 마감 후 대기실장봇 → 캔들기록봇 → 문지기봇을 순차 실행하는 Windows Task Scheduler 기반 자동화 시스템입니다.

## 파이프라인 순서

```
[장 마감 후 15:35]
1️⃣ 대기실장봇 (build_candidate_pool.py)
   → candidate_pool_YYYYMMDD.json 생성
   
2️⃣ 캔들기록봇 (collect_ohlcv.py)
   → ohlcv_YYYYMMDD.csv 생성
   
3️⃣ 문지기봇 (prepare_tomorrow.py)
   → watchlist_YYYYMMDD.json 생성
```

## 실행 방법

### 1. 배치 파일 직접 실행 (테스트)

```bash
scripts\run\run_post_market_pipeline.bat
```

**성공 기준:**
- `logs/post_market_YYYYMMDD.log` 파일 생성
- 로그 마지막 줄에 `[SUCCESS] Pipeline Finished` 표시

### 2. 스케줄러 등록

```bash
# 스케줄러 등록
scripts\scheduler\setup_post_market_pipeline.bat

# 스케줄러 제거
scripts\scheduler\remove_post_market_pipeline.bas
```

**주의사항:**
- 관리자 권한으로 실행해야 할 수 있습니다
- 배치 파일을 먼저 테스트한 후 스케줄러에 등록하세요

## 스케줄러 설정 상세

### 작업 정보
- **이름**: `PostMarketPipeline`
- **실행 시간**: 매일 15:35
- **실행 파일**: `scripts\run\run_post_market_pipeline.bat`
- **작업 디렉토리**: 프로젝트 루트

### 설정 권장사항

**일반 탭:**
- ✅ 가장 높은 권한으로 실행
- ✅ 사용자 로그온 여부와 관계없이 실행

**트리거 탭:**
- 일정: 매일
- 시간: 15:35
- ✅ 예약 시간 이후 가능한 빨리 실행

**동작 탭:**
- 프로그램/스크립트: `C:\주식자동매매_개발관련\Restapi_SebinStock_VER1\scripts\run\run_post_market_pipeline.bat`
- 시작 위치: `C:\주식자동매매_개발관련\Restapi_SebinStock_VER1`

**설정 탭:**
- ✅ 중복 실행 방지

## 로그 파일

### 위치
```
logs/post_market_YYYYMMDD.log
```

### 로그 내용
- 각 단계별 시작/성공/실패 상태
- Python 스크립트의 모든 출력
- 오류 메시지 및 스택 트레이스

### 로그 확인 방법
```bash
# 최신 로그 확인
type logs\post_market_20260107.log

# 또는 메모장으로 열기
notepad logs\post_market_20260107.log
```

## 결과 파일 확인

매일 다음 파일들이 생성되는지 확인하세요:

1. **대기실장봇 출력**
   - `scout_selector/output/candidate_pool_YYYYMMDD.json`

2. **캔들기록봇 출력**
   - `scout_selector/data/ohlcv_YYYYMMDD.csv`

3. **문지기봇 출력**
   - `scout_selector/output/watchlist_YYYYMMDD.json`
   - `scout_selector/output/latest_watchlist.json`

## 오류 처리

### 앞 단계 실패 시
- 다음 단계는 실행되지 않습니다
- 로그 파일에 `[FAIL]` 메시지 기록
- 배치 파일이 오류 코드로 종료

### 개별 단계 실패
- 각 단계는 독립적으로 실행됩니다
- 실패 시 해당 단계만 `[FAIL]` 표시
- 다음 단계는 실행되지 않습니다

## 수동 실행 (긴급 시)

스케줄러가 실행되지 않았거나 오류가 발생한 경우:

```bash
# 전체 파이프라인 수동 실행
scripts\run\run_post_market_pipeline.bat

# 또는 개별 실행
python scout_selector\build_candidate_pool.py
python scout_selector\collect_ohlcv.py
python scout_selector\prepare_tomorrow.py
```

## 문제 해결

### 스케줄러가 실행되지 않는 경우
1. 작업 스케줄러에서 작업 상태 확인
2. 로그 파일 확인 (`logs/post_market_YYYYMMDD.log`)
3. 배치 파일 직접 실행하여 테스트
4. 관리자 권한으로 스케줄러 재등록

### Python 모듈 오류
- `venv`에 필요한 패키지가 설치되어 있는지 확인
- `pip install -r requirements-run.txt` 실행

### 경로 오류
- 배치 파일의 `PROJECT_ROOT` 경로 확인
- 한글 경로 문제가 있는 경우 경로를 영문으로 변경 고려

---

**버전**: 1.0.0  
**최종 업데이트**: 2026-01-07






