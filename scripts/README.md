# 스크립트 디렉터리

프로젝트의 모든 유틸리티 스크립트(BAT, PS1, PY)를 관리하는 디렉터리입니다.

## 📁 디렉터리 구조

```
scripts/
├── run/              # 사람이 직접 실행하는 스크립트
├── scheduler/        # 작업 스케줄러 설정/해제 스크립트
└── maintenance/      # 유지보수 및 관리용 유틸리티
```

---

## 🚀 실행 스크립트 (`run/`)

사람이 직접 실행하는 스크립트들입니다.

### 정찰봇 관련
- `run_scout_bot.bat` / `run_scout_bot.ps1`: 정찰봇 실행

### 분석 관련
- `run_post_market_analyzer.bat`: Post-Market Analyzer 실행 (수동)
- `run_post_market_analyzer_auto.bat`: Post-Market Analyzer 자동 실행 (그래프 포함)
- `view_scout_results.bat`: 정찰 결과 간단 확인

### 신호 수집 관련
- `run_signals_collector.bat`: 신호 수집 실행

### Post-Market 파이프라인
- `run_post_market_pipeline.bat`: 대기실장봇 → 캔들기록봇 → 문지기봇 순차 실행

---

## ⏰ 스케줄러 스크립트 (`scheduler/`)

Windows 작업 스케줄러 설정/해제 스크립트들입니다.

### Post-Market Analyzer 스케줄러
- `setup_scheduler.bat`: 스케줄러 설정 (메인)
- `setup_scheduler.ps1`: 스케줄러 설정 (PowerShell)
- `setup_scheduler_simple.ps1`: 스케줄러 설정 (간단 버전)
- `setup_scheduler_schtasks.bat`: 스케줄러 설정 (schtasks 사용)
- `remove_scheduler.bat`: 스케줄러 제거 (메인)
- `remove_scheduler.ps1`: 스케줄러 제거 (PowerShell)
- `remove_scheduler_schtasks.bat`: 스케줄러 제거 (schtasks 사용)

### 신호 수집 스케줄러
- `setup_signals_collector_scheduler.bat`: 신호 수집 스케줄러 설정
- `remove_signals_collector_scheduler.bat`: 신호 수집 스케줄러 제거

### Post-Market 파이프라인 스케줄러
- `setup_post_market_pipeline.bat`: Post-Market 파이프라인 스케줄러 설정 (매일 15:35)
- `remove_post_market_pipeline.bat`: Post-Market 파이프라인 스케줄러 제거

---

## 🔧 유지보수 스크립트 (`maintenance/`)

유지보수 및 관리용 유틸리티 스크립트들입니다.

- `check_scout_data.py`: 오늘 수집된 정찰 데이터 검토 스크립트

---

## 📝 사용 방법

### 실행 스크립트
```bash
# 정찰봇 실행
scripts\run\run_scout_bot.bat

# 분석 실행
scripts\run\run_post_market_analyzer.bat

# 신호 수집 실행
scripts\run\run_signals_collector.bat

# Post-Market 파이프라인 실행
scripts\run\run_post_market_pipeline.bat
```

### 스케줄러 설정
```bash
# Post-Market Analyzer 스케줄러 설정
scripts\scheduler\setup_scheduler.bat

# 신호 수집 스케줄러 설정
scripts\scheduler\setup_signals_collector_scheduler.bat

# Post-Market 파이프라인 스케줄러 설정
scripts\scheduler\setup_post_market_pipeline.bat
```

### 유지보수
```bash
# 정찰 데이터 검토
python scripts\maintenance\check_scout_data.py
```

---

## ⚠️ 주의사항

- 모든 스크립트는 프로젝트 루트를 기준으로 동작합니다.
- 스케줄러 스크립트는 관리자 권한이 필요할 수 있습니다.
- 스크립트 내용은 수정하지 마세요. 경로 참조만 최소한으로 조정되었습니다.


