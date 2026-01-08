# 문지기봇 입력 포맷

외부 신호(조건식·뉴스)를 문지기봇이 사용하는 표준 입력 포맷

---

## 📁 디렉토리 구조

```
gatekeeper_bot/
├── input/                          ← 오늘 날짜 파일만 유지
│   ├── conditions/
│   │   └── conditions_YYYYMMDD.json
│   ├── news/
│   │   └── news_YYYYMMDD.json
│   └── README.md
│
└── history/                        ← 과거 파일 자동 아카이브
    └── input/
        ├── conditions/
        │   └── conditions_YYYYMMDD.json
        └── news/
            └── news_YYYYMMDD.json
```

### 📌 중요 사항

- **오늘 날짜 파일만 사용**: `build_theme_score_map`은 지정된 날짜의 파일만 읽습니다
- **자동 아카이브**: 과거 날짜 파일은 자동으로 `history/input/`으로 이동됩니다
- **히스토리 보존**: 과거 신호는 히스토리 디렉토리에 보관되어 나중에 분석 가능합니다

---

## 📄 조건식 입력 포맷

**파일**: `input/conditions/conditions_YYYYMMDD.json`

```json
{
  "date": "20260105",
  "source": "kiwoom_condition",
  "conditions": [
    {
      "condition_name": "AI_관련주",
      "symbols": ["035420", "030200", "064350"]
    },
    {
      "condition_name": "거래량_급증",
      "symbols": ["068270", "096530"]
    }
  ]
}
```

### 필드 설명

- `date`: 날짜 (YYYYMMDD)
- `source`: 데이터 출처 (예: "kiwoom_condition")
- `conditions`: 조건식 배열
  - `condition_name`: 조건식 이름 (분석용)
  - `symbols`: 종목 코드 배열

### 점수 정책

- 조건식에 포함된 종목 → `theme_score = 1.0`
- 출처: `condition:{조건식_이름}` 형식으로 기록됩니다

---

## 📰 뉴스 입력 포맷

**파일**: `input/news/news_YYYYMMDD.json`

```json
{
  "date": "20260105",
  "source": "naver_news",
  "items": [
    {
      "symbol": "035420",
      "headline": "네이버, AI 검색 고도화 발표",
      "keywords": ["AI", "검색"],
      "published_at": "2026-01-05T09:12:00"
    },
    {
      "symbol": "068270",
      "headline": "바이오 업종 강세",
      "keywords": ["바이오"],
      "published_at": "2026-01-05T10:30:00"
    }
  ]
}
```

### 필드 설명

- `date`: 날짜 (YYYYMMDD)
- `source`: 데이터 출처 (예: "naver_news")
- `items`: 뉴스 아이템 배열
  - `symbol`: 종목 코드
  - `headline`: 뉴스 제목
  - `keywords`: 키워드 배열
  - `published_at`: 발행 시각 (ISO 8601)

### 점수 정책

- 뉴스 1건 → `theme_score = 0.3`
- 뉴스 3건 이상 → `theme_score = 1.0`
- 조건식과 뉴스 둘 다 있으면 → `theme_score = 1.0` (최대값 유지)
- 출처: `news:{건수}건({키워드1},{키워드2})` 형식으로 기록됩니다

---

## 🔄 데이터 흐름

```
[ 조건식 / 뉴스 수집 ]
          ↓
[ gatekeeper_bot/input/ (오늘 날짜만) ]
          ↓
[ theme_score_builder ]
    ├─ 오늘 날짜 파일 읽기
    ├─ 과거 파일 → history/ 이동
    └─ {symbol: {score, sources}} 생성
          ↓
[ theme_score_map ]
          ↓
[ selector.py (문지기봇 핵심 엔진) ]
    └─ reason에 sources 포함
```

**문지기봇 핵심 엔진은 입력 원천을 모른다**  
**문지기봇 핵심 엔진은 오직 theme_score_map만 받는다**  
**출처 정보는 reason에 포함되어 저장됩니다**

---

## 📝 사용 예시

### 조건식 파일 생성

```python
import json
from pathlib import Path

data = {
    "date": "20260105",
    "source": "kiwoom_condition",
    "conditions": [
        {
            "condition_name": "AI_관련주",
            "symbols": ["035420", "030200"]
        }
    ]
}

input_dir = Path("gatekeeper_bot/input/conditions")
input_dir.mkdir(parents=True, exist_ok=True)

with open(input_dir / "conditions_20260105.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

### 뉴스 파일 생성

```python
import json
from pathlib import Path

data = {
    "date": "20260105",
    "source": "naver_news",
    "items": [
        {
            "symbol": "035420",
            "headline": "네이버, AI 검색 고도화 발표",
            "keywords": ["AI", "검색"],
            "published_at": "2026-01-05T09:12:00"
        }
    ]
}

input_dir = Path("gatekeeper_bot/input/news")
input_dir.mkdir(parents=True, exist_ok=True)

with open(input_dir / "news_20260105.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

---

## ⚠️ 주의사항

1. **파일명 규칙**: `conditions_YYYYMMDD.json`, `news_YYYYMMDD.json`
2. **인코딩**: UTF-8
3. **종목 코드**: 6자리 문자열 (예: "005930")
4. **중복 허용**: 같은 종목이 여러 조건식/뉴스에 포함되어도 OK (builder에서 처리)
5. **날짜 필터**: 오늘 날짜 파일만 사용됩니다 (과거 파일은 자동으로 히스토리로 이동)
6. **출처 정보**: theme_score reason에 `sources` 필드로 포함됩니다

## 📦 히스토리 관리

과거 신호 파일은 자동으로 `gatekeeper_bot/history/input/` 디렉토리로 이동됩니다:

- `history/input/conditions/conditions_YYYYMMDD.json`
- `history/input/news/news_YYYYMMDD.json`

이 파일들은 나중에 분석이나 검증에 사용할 수 있습니다.



