# Signals Collector

신호 수집 모듈

조건식/뉴스를 수집하여 `scout_selector/input/` 에 JSON 파일로 저장합니다.

---

## 📁 디렉토리 구조

```
signals_collector/
├── collectors/
│   ├── condition_kiwoom.py    # 조건식 수집기
│   └── news_provider.py       # 뉴스 수집기
├── run_collect.py              # 실행 엔트리포인트
└── README.md
```

---

## 🚀 사용 방법

### 기본 실행 (오늘 날짜)

```bash
python signals_collector/run_collect.py
```

### 특정 날짜 지정

```bash
python signals_collector/run_collect.py --date 20260105
```

### 특정 조건식만 수집

```bash
python signals_collector/run_collect.py --conditions "AI_관련주" "거래량_급증"
```

---

## 📋 수집 항목

### 1. 조건식 (Conditions)

**수집기**: `collectors/condition_kiwoom.py`

**출력**: `scout_selector/input/conditions/conditions_YYYYMMDD.json`

**기능**:
- 키움 API에서 조건식 목록 조회
- 각 조건식별 종목 리스트 수집
- JSON 형식으로 저장

**실패 시**: 빈 JSON 파일 생성 (파이프라인 안전장치)

### 2. 뉴스 (News)

**수집기**: `collectors/news_provider.py`

**출력**: `scout_selector/input/news/news_YYYYMMDD.json`

**기능**:
- 뉴스 API에서 종목별 뉴스 수집
- 키워드 추출
- JSON 형식으로 저장

**현재 상태**: MOCK 모드 (실제 API 연동 필요)

**실패 시**: 빈 JSON 파일 생성 (파이프라인 안전장치)

---

## ⏰ 실행 타이밍

**권장**: 장 마감 후 1회 실행

```
장 마감 (15:30)
    ↓
signals_collector/run_collect.py 실행
    ↓
scout_selector/input/conditions/*.json 생성
scout_selector/input/news/*.json 생성
    ↓
scout_selector/runner.py 실행
    ↓
theme_score_map 생성
watchlist_YYYYMMDD.json 출력
```

---

## 🔧 설정

### 조건식 수집 설정

`run_collect.py`에서 `condition_names` 파라미터로 수집할 조건식 지정:

```python
# 모든 조건식 수집
collect_conditions(output_dir, date, condition_names=None)

# 특정 조건식만 수집
collect_conditions(output_dir, date, condition_names=["AI_관련주", "거래량_급증"])
```

### 뉴스 수집 설정

`run_collect.py`에서 `use_api` 파라미터로 실제 API 사용 여부 지정:

```python
# MOCK 모드 (기본)
collect_news(output_dir, date, use_api=False)

# 실제 API 사용 (네이버 뉴스 RSS 크롤링)
collect_news(output_dir, date, use_api=True, api_config={...})
```

**뉴스 키워드 자동 추출**:
- 주식 관련 키워드 자동 매칭 (AI, 반도체, 바이오, 전기차 등)
- 뉴스 제목에서 키워드 추출하여 `keywords` 필드에 저장

---

## 🛡️ 안전장치

### 파이프라인 안전장치

수집 실패 시에도 **빈 JSON 파일을 생성**하여 파이프라인이 끊기지 않도록 합니다:

```json
{
  "date": "20260105",
  "source": "kiwoom_condition",
  "conditions": []
}
```

이렇게 하면:
- `theme_score_builder`가 파일을 읽을 수 있음
- `theme_score_map`이 빈 딕셔너리로 생성됨
- selector가 정상 동작함 (theme 점수만 0)

---

## 📝 구현 완료

- [x] 뉴스 API 실제 연동 (네이버 뉴스 RSS 크롤링 구조 추가)
- [x] 뉴스 키워드 자동 추출 (주식 관련 키워드 자동 매칭)
- [x] 수집 실패 알림 (텔레그램)
- [x] 스케줄러 설정 (장 마감 후 자동 실행)

## 📝 추가 개선 가능 항목

- [ ] 뉴스 API 실제 연동 (네이버 뉴스 API, 다음 뉴스 API 등)
- [ ] 종목명 매핑 API 연동 (종목 코드 → 종목명)
- [ ] 수집 결과 검증 로직
- [ ] 수집 성공 알림 (선택적)

---

## 🔗 관련 모듈

- **scout_selector/theme_score_builder.py**: 수집된 JSON을 읽어서 theme_score_map 생성
- **scout_selector/runner.py**: theme_score_map을 사용하여 watchlist 생성

---

## ⚠️ 주의사항

1. **오늘 날짜만 저장**: 수집기는 오늘 날짜 파일만 생성합니다
2. **과거 파일 자동 이동**: `theme_score_builder`가 과거 파일을 `history/`로 이동합니다
3. **독립 모듈**: 수집기는 `scout_selector`나 `scout_bot`을 import하지 않습니다
4. **파일만 쓰기**: 수집기는 파일만 쓰고, selector는 파일만 읽습니다
5. **텔레그램 알림**: 수집 실패 시 자동으로 텔레그램 알림 전송 (설정 필요)

## 🕐 스케줄러 설정

### Windows Task Scheduler 설정

**설정**:
```bash
setup_signals_collector_scheduler.bat
```

**제거**:
```bash
remove_signals_collector_scheduler.bat
```

**기본 설정**:
- 실행 시간: 매일 15:35 (장 마감 후)
- 작업 이름: `SignalsCollector_Daily`

**수동 확인**:
```bash
schtasks /Query /TN "SignalsCollector_Daily"
```

