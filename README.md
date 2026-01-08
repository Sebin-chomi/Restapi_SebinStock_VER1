# 주식 자동매매 시스템 - Restapi_SebinStock_VER1

## 📋 개요

이 프로젝트는 주식 자동매매를 위한 통합 시스템으로, 다음 주요 컴포넌트로 구성됩니다:

1. **정찰봇 (Scout Bot)**: 시장 관찰 및 패턴 감지
2. **문지기봇 (Gatekeeper Bot)**: 일일 관찰 종목 선정
3. **Post-Market Analyzer**: 장 마감 후 시장 분석
4. **자동매매 시스템**: 매수/매도 실행

---

## 🏗️ 시스템 구조

```
[정찰봇]
  └─ JSONL 기록 (하루치)
      └─ records/scout/YYYY-MM-DD/{종목코드}.jsonl

[Post-Market Analyzer]   ← 장 마감 후 분석
  ├─ 정찰 JSONL 읽기
  ├─ observer / reason 집계
  ├─ (선택) 상위 100 결과 읽기
  ├─ 시장 성격 요약 생성
  └─ 일일 평가 기록 저장
      └─ records/analysis/YYYY-MM-DD/daily_analysis.{json,txt}

[전략 / 딥러닝 / 회고]
  └─ 필요할 때 이 결과를 참고
```

---

## 🚀 주요 기능

### 1. 정찰봇 (Scout Bot)

**위치**: `test/scout_bot/`

**기능**:
- 매일 09:30 장 시작 시 자동 실행
- Watchlist 종목을 2분 간격으로 관찰
- Observer 패턴 감지 (Volume, BaseCandle, Box)
- 실시간 관찰 결과를 JSONL 형식으로 기록

**실행 방법**:
```bash
# 방법 1: 모듈 실행
python -m test.scout_bot.day_main

# 방법 2: 배치 스크립트 (Windows)
run_scout_bot.bat
```

**기록 위치**:
- `records/scout/YYYY-MM-DD/{종목코드}.jsonl`

**텔레그램 명령어**:
- `/add 종목코드` - 종목 추가
- `/remove 종목코드` - 종목 제거
- `/list` - 현재 watchlist 확인
- `/status` - 상태 확인

---

### 2. 문지기봇 (Gatekeeper Bot)

**위치**: `scout_selector/` (또는 `gatekeeper_bot/`)

**문서**: [문지기봇 문서](./docs/gatekeeper-bot/README.md) 참조

**역할**:
- 장 마감 후 배치 프로세스로 실행
- 전 종목 대상 입구 필터 및 1·2차 필터링 수행
- 정찰봇이 감시할 종목 후보군 생성

**기능**:
- 매일 자동으로 8종목 선정 (largecap 2 + volume 2 + structure 2 + theme 2)
- Cold Start 지원 (데이터 부족 시 warmup 모드)
- Warm-up → Normal 자동 전환 (20일 데이터 기준)
- 선정 사유(reason) 포함

**실행 방법**:
```bash
# 내일 watchlist 자동 생성 (장 마감 후 실행 권장)
python scout_selector/prepare_tomorrow.py

# 수동 선정
python scout_selector/manual_select.py

# 직접 실행 (오늘 날짜 기준)
python scout_selector/runner.py
```

**출력 파일**:
- `scout_selector/output/watchlist_YYYYMMDD.json` (문지기봇 출력 스냅샷)
- `scout_selector/output/latest_watchlist.json`

**문서**:
- [문지기봇 문서](./docs/gatekeeper-bot/README.md)
- [출력 형식 명세](./scout_selector/output/WATCHLIST_FORMAT_SPEC.md)

**선정 구조**:
```json
{
  "date": "20260105",
  "phase": "normal",
  "largecap": [
    {
      "symbol": "005930",
      "bucket": "largecap",
      "score": 1.0,
      "reason": {
        "close": 75000,
        "turnover_krw": 1104567890000
      }
    }
  ],
  "volume": [...],
  "structure": [...],
  "theme": [...]
}
```

---

### 3. Post-Market Analyzer

**위치**: `test/framework/analyzer/`

**기능**:
- 장 마감 후 일일 정찰 기록 분석
- Observer/Reason 집계
- 시장 성격 요약 생성 (ACTIVE/MODERATE/QUIET/DEAD)
- 일일 평가 기록 저장

**실행 방법**:
```bash
# 오늘 날짜 분석
python -m test.framework.analyzer.run_analyzer

# 특정 날짜 분석
python -m test.framework.analyzer.run_analyzer 2026-01-01

# 상위 100 결과 포함
python -m test.framework.analyzer.run_analyzer 2026-01-01 --top100

# 그래프 포함 분석
python -m test.framework.analyzer.run_analyzer 2026-01-01 --with-graphs

# Windows 배치 스크립트
run_post_market_analyzer.bat
run_post_market_analyzer.bat 2026-01-01

# 자동 실행 (그래프 포함) - 장 마감 후 자동 실행용
run_post_market_analyzer_auto.bat
python test/framework/analyzer/auto_analyzer.py
```

**출력 파일**:
- `records/analysis/YYYY-MM-DD/daily_analysis.json` (기계용)
- `records/analysis/YYYY-MM-DD/daily_analysis.txt` (사람용)
- `records/analysis/YYYY-MM-DD/daily_report.json` (스키마 기반 계약 파일)
- `records/analysis/YYYY-MM-DD/daily_graphs/` (그래프 디렉토리, `--with-graphs` 사용 시)
  - `cycle_outcomes.png` - Cycle 종료 유형 분포
  - `cycle_duration_hist.png` - 유지 시간 분포
  - `time_of_day_cycles.png` - 장중 시간대별 Cycle 발생 수

**분석 내용**:
- 총 정찰 횟수 및 관찰 종목 수
- Observer 트리거 통계
- Box 형성 통계
- Base Candle 존재 통계
- 세션별 분포 (OPEN/NORMAL)
- 이벤트 미발생 사유
- Watchlist 선정 사유 (bucket별)
- 시장 성격 분류 및 설명

---

## 📁 디렉토리 구조

```
Restapi_SebinStock_VER1/
├── test/
│   ├── scout_bot/          # 정찰봇 메인
│   │   └── day_main.py
│   ├── framework/
│   │   ├── analyzer/        # Post-Market Analyzer
│   │   │   ├── post_market_analyzer.py
│   │   │   └── run_analyzer.py
│   │   ├── engine/          # 정찰 엔진
│   │   ├── observer/        # 패턴 감지
│   │   ├── record/          # 기록 관리
│   │   └── watchlist/       # Watchlist 관리
│   └── config_test.py       # 테스트 환경 설정
├── scout_selector/          # 문지기봇 (종목 선정 시스템)
│   ├── selector.py          # 문지기봇 핵심 엔진
│   ├── runner.py            # 문지기봇 실행 진입점 (오늘)
│   ├── prepare_tomorrow.py  # 문지기봇 실행 진입점 (내일)
│   ├── manual_select.py     # 수동 종목 선정
│   ├── config/
│   │   └── selector.yaml     # 설정 파일
│   ├── output/              # 출력 파일 (watchlist_YYYYMMDD.json)
│   └── docs/                # 문지기봇 문서 (설계/구현/검증)
├── docs/                    # 프로젝트 문서 인덱스
│   ├── README.md            # 문서 인덱스
│   ├── governance.md        # 문서 거버넌스 가이드
│   ├── gatekeeper-bot/      # 문지기봇 문서
│   ├── scout-bot/           # 정찰봇 문서
│   └── api/                 # API 문서
├── records/
│   ├── scout/               # 정찰 기록 (JSONL)
│   │   └── YYYY-MM-DD/
│   │       └── {종목코드}.jsonl
│   └── analysis/            # 분석 결과
│       └── YYYY-MM-DD/
│           ├── daily_analysis.json
│           └── daily_analysis.txt
├── run_scout_bot.bat        # 정찰봇 실행 스크립트
└── run_post_market_analyzer.bat  # 분석기 실행 스크립트
```

---

## 🔧 설정

### 텔레그램 설정

`test/config_test.py`에서 텔레그램 봇 토큰을 설정해야 합니다:

```python
telegram_token = "YOUR_BOT_TOKEN"
telegram_chat_id = "YOUR_CHAT_ID"

# 별칭 (호환성)
TELEGRAM_BOT_TOKEN = telegram_token
TELEGRAM_CHAT_ID = telegram_chat_id
```

### 문지기봇 설정

`scout_selector/config/selector.yaml`에서 선정 기준을 설정할 수 있습니다.

---

## 📚 문서

프로젝트의 모든 문서는 [docs/](./docs/README.md) 디렉토리에서 관리됩니다.

- **[문서 인덱스](./docs/README.md)**: 전체 문서 목록
- **[문서 거버넌스](./docs/governance.md)**: 문서 작성 가이드
- **[문지기봇 문서](./docs/gatekeeper-bot/README.md)**: 문지기봇 상세 문서
- **[정찰봇 문서](./docs/scout-bot/README.md)**: 정찰봇 문서
- **[신호 수집기 문서](./docs/signals-collector/README.md)**: 신호 수집기 문서

---

## 📊 일일 워크플로우

### 1. 전날 밤 (또는 당일 아침)

**문지기봇 실행**:
```bash
python scout_selector/prepare_tomorrow.py
```

또는 수동 선정:
```bash
python scout_selector/manual_select.py
```

**결과**: `scout_selector/output/watchlist_YYYYMMDD.json` 생성 (문지기봇 출력 스냅샷)

---

### 2. 장 시작 (09:30)

**정찰봇 자동 실행**:
- `test/scout_bot/day_main.py`가 자동으로 실행됨
- Watchlist를 자동으로 로드
- 2분 간격으로 관찰 시작
- 관찰 결과를 `records/scout/YYYY-MM-DD/`에 기록

**Cold Start 시나리오**:
- Watchlist JSON이 없으면 대형주만 포함
- 텔레그램 `/add` 명령어로 종목 추가 가능

---

### 3. 장 마감 후

**Post-Market Analyzer 실행** (수동):
```bash
python -m test.framework.analyzer.run_analyzer
```

**Post-Market Analyzer 자동 실행** (그래프 포함, 매일 17:00):
- 자동 설정: `setup_scheduler.bat` 실행 (권장)
- Windows 작업 스케줄러 수동 설정: `setup_auto_analyzer.md` 참고
- 수동 실행: `run_post_market_analyzer_auto.bat`

**결과**: 
- `records/analysis/YYYY-MM-DD/daily_analysis.{json,txt}` 생성
- `records/analysis/YYYY-MM-DD/daily_report.json` 생성 (스키마 기반)
- `records/analysis/YYYY-MM-DD/daily_graphs/` 생성 (자동 실행 시)

---

## ⚠️ 중요 사항

### Post-Market Analyzer와 정찰봇의 관계

**Post-Market Analyzer는 정찰봇의 자료 수집에 영향을 미치지 않습니다.**

- **정찰봇**: `records/scout/`에 JSONL 파일을 **쓰기만** 함
- **Post-Market Analyzer**: `records/scout/`에서 JSONL 파일을 **읽기만** 함
- **완전히 독립적인 모듈**: 서로 간섭 없음

따라서 Post-Market Analyzer를 추가해도 내일 실행될 정찰봇의 자료 수집에는 **전혀 영향이 없습니다**.

---

## 🔍 데이터 흐름

```
[선정 시스템]
  ↓ watchlist_YYYYMMDD.json 생성
[정찰봇]
  ↓ records/scout/YYYY-MM-DD/{종목코드}.jsonl 기록
[Post-Market Analyzer] (장 마감 후)
  ↓ records/analysis/YYYY-MM-DD/daily_analysis.{json,txt} 생성
[전략/딥러닝/회고]
  ↓ 분석 결과 참고
```

---

## 🛠️ 개발 환경

- Python 3.14+
- 가상환경: `venv/`
- 주요 패키지: `requirements-run.txt` 참고

---

## 📝 라이선스

프로젝트 내부용

---

## 📞 문의

프로젝트 내부 이슈 트래커 사용


