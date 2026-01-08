# Post-Market Analyzer 자동 실행 설정 가이드

## 📋 개요

장 마감 후 자동으로 Post-Market Analyzer를 실행하여 분석 및 그래프를 생성합니다.

**매일 17:00에 자동 실행됩니다.**

---

## 🚀 방법 1: 자동 설정 스크립트 (권장)

### 실행 방법

```bash
# Windows 배치 스크립트 (관리자 권한 권장)
setup_scheduler.bat

# 또는 PowerShell 직접 실행
powershell.exe -ExecutionPolicy Bypass -File setup_scheduler.ps1
```

이 스크립트는 자동으로 Windows 작업 스케줄러에 등록합니다:
- **실행 시간**: 매일 17:00
- **작업 이름**: `Post-Market Analyzer 자동 실행`
- **그래프 포함**: 자동으로 생성됨

### 스케줄러 제거

```bash
# 제거 스크립트
remove_scheduler.bat

# 또는 PowerShell 직접 실행
powershell.exe -ExecutionPolicy Bypass -File remove_scheduler.ps1
```

---

## 🚀 방법 2: 배치 스크립트 실행 (수동)

### 실행 방법

```bash
# 방법 1: 배치 스크립트
run_post_market_analyzer_auto.bat

# 방법 2: Python 스크립트 직접 실행
python test/framework/analyzer/auto_analyzer.py
```

---

## ⏰ 방법 3: Windows 작업 스케줄러 수동 설정

### 1. 작업 스케줄러 열기

1. Windows 검색에서 "작업 스케줄러" 검색
2. 작업 스케줄러 열기

### 2. 기본 작업 만들기

1. **작업 만들기** 클릭
2. **일반** 탭:
   - 이름: `Post-Market Analyzer 자동 실행`
   - 설명: `장 마감 후 일일 분석 및 그래프 생성`
   - **"사용자가 로그온할 때만 실행"** 선택
   - **"가장 높은 수준의 권한으로 실행"** 체크 (필요시)

### 3. 트리거 설정

1. **트리거** 탭 → **새로 만들기**
2. 설정:
   - 작업 시작: **일정에 따라**
   - 설정: **매일**
   - 시작 날짜: 오늘 날짜
   - 시작 시간: **17:00** (장 마감 후)
   - 반복: **매일**
   - 사용: **체크**

### 4. 작업 설정

1. **동작** 탭 → **새로 만들기**
2. 설정:
   - 동작: **프로그램 시작**
   - 프로그램/스크립트: 
     ```
     C:\주식자동매매_개발관련\Restapi_SebinStock_VER1\run_post_market_analyzer_auto.bat
     ```
   - 시작 위치(옵션):
     ```
     C:\주식자동매매_개발관련\Restapi_SebinStock_VER1
     ```

### 5. 조건 설정

1. **조건** 탭:
   - **"작업을 시작하기 위해 컴퓨터가 AC 전원에 연결되어 있어야 함"** 체크 해제
   - **"작업을 시작하기 위해 컴퓨터가 유휴 상태여야 함"** 체크 해제

### 6. 설정

1. **설정** 탭:
   - **"작업이 실행 중이면 즉시 중지"** 체크 해제
   - **"작업이 요청된 시간에 실행되지 못한 경우 즉시 작업 실행"** 체크
   - **"작업이 실패할 경우 다시 시작"** 체크 (재시도 횟수: 3)

### 7. 저장

1. **확인** 클릭
2. 비밀번호 입력 (필요시)

---

## 🔍 실행 확인

### 로그 확인

1. 작업 스케줄러 → **작업 스케줄러 라이브러리**
2. `Post-Market Analyzer 자동 실행` 작업 선택
3. **기록** 탭에서 실행 이력 확인

### 결과 파일 확인

```
records/analysis/YYYY-MM-DD/
├── daily_analysis.json
├── daily_analysis.txt
├── daily_report.json
└── daily_graphs/
    ├── cycle_outcomes.png
    ├── cycle_duration_hist.png
    └── time_of_day_cycles.png
```

---

## ⚠️ 주의사항

1. **Python 경로 확인**: 배치 스크립트에서 Python이 PATH에 있는지 확인
2. **프로젝트 경로**: 절대 경로를 사용하거나 상대 경로가 올바른지 확인
3. **권한**: 필요한 경우 관리자 권한으로 실행
4. **장 마감 시간**: 한국 시간 기준 15:30 장 마감, 15:35 이후 실행 권장

---

## 🛠️ 문제 해결

### 실행되지 않는 경우

1. **작업 스케줄러 기록 확인**
   - 작업 스케줄러 → 기록 탭에서 오류 메시지 확인

2. **수동 실행 테스트**
   ```bash
   run_post_market_analyzer_auto.bat
   ```

3. **Python 경로 확인**
   ```bash
   python --version
   ```

4. **의존성 확인**
   ```bash
   python -c "import matplotlib; print('OK')"
   ```

### 그래프가 생성되지 않는 경우

- matplotlib 설치 확인:
  ```bash
  python -m pip install matplotlib numpy
  ```

---

## 📝 참고

- **실행 시간**: 매일 15:35 (장 마감 후)
- **그래프 포함**: 자동으로 생성됨
- **로그**: 작업 스케줄러 기록에서 확인 가능

