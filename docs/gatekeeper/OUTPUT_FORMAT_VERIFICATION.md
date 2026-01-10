# prepare_tomorrow.py 출력 형식 검증

## ✅ 코드 검증 결과

### 1. 메타 정보 (`meta`) 필드 확인

**코드 위치:** `prepare_tomorrow.py` 177-184줄

```python
output = {
    "meta": {
        "date": tomorrow_str,
        "created_at": created_at,
        "phase": phase,
        "gatekeeper_version": GATEKEEPER_BOT_VERSION,  # ✅ 명시적 필드
        "gatekeeper_bot_version": GATEKEEPER_BOT_VERSION,  # ✅ 호환성 유지
    },
    ...
}
```

**검증 결과:** ✅ 최신 형식 준수
- `gatekeeper_version` 필드 포함
- `gatekeeper_bot_version` 필드 포함 (호환성 유지)

---

### 2. 종목 항목 필드 확인

**코드 위치:** `selector.py`의 `select_watchlist()` 함수

각 종목 항목은 다음 필드를 포함합니다:

#### 대형주 (`largecap`)
- ✅ `symbol`: 종목코드
- ✅ `category`: "largecap"
- ✅ `selection_reason`: 선정 사유 요약
- ✅ `indicators`: 주요 지표 값

**코드 위치:** `selector.py` 533-547줄

#### 거래량형 (`volume`)
- ✅ `symbol`: 종목코드
- ✅ `category`: "volume"
- ✅ `selection_reason`: 선정 사유 요약
- ✅ `indicators`: 주요 지표 값

**코드 위치:** `selector.py` 655-672줄

#### 구조형 (`structure`)
- ✅ `symbol`: 종목코드
- ✅ `category`: "structure"
- ✅ `structure_score`: 구조 점수 (0~100점) - **구조형만**
- ✅ `selection_reason`: 선정 사유 요약
- ✅ `indicators`: 주요 지표 값

**코드 위치:** `selector.py` 724-746줄, 761-781줄

#### 테마형 (`theme`)
- ✅ `symbol`: 종목코드
- ✅ `category`: "theme"
- ✅ `selection_reason`: 선정 사유 요약
- ✅ `indicators`: 주요 지표 값

**코드 위치:** `selector.py` 826-838줄

---

### 3. 출력 파일 생성 확인

**코드 위치:** `prepare_tomorrow.py` 191-193줄

```python
out_file = OUTPUT_DIR / f"watchlist_{tomorrow_str}.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
```

**검증 결과:** ✅ 정상 생성
- 파일명: `watchlist_YYYYMMDD.json` 형식
- 인코딩: UTF-8
- 들여쓰기: 2칸 (가독성)

---

## 📋 최신 형식 필드 체크리스트

| 필드 | 위치 | 코드 확인 | 상태 |
|------|------|----------|------|
| `meta.gatekeeper_version` | 최상위 | `prepare_tomorrow.py:182` | ✅ |
| `category` | 각 종목 | `selector.py` (모든 카테고리) | ✅ |
| `selection_reason` | 각 종목 | `selector.py` (모든 카테고리) | ✅ |
| `structure_score` | 구조형만 | `selector.py:729, 766` | ✅ |
| `indicators` | 각 종목 | `selector.py` (모든 카테고리) | ✅ |

---

## ✅ 결론

**코드 검증 결과:** `prepare_tomorrow.py`는 최신 형식으로 정상 출력됩니다.

모든 필수 메타 필드가 포함되어 있으며, 각 종목 항목에도 필요한 필드가 모두 포함되어 있습니다.

---

## 🔄 다음 단계

실제 실행 후 생성된 파일을 확인하여 최종 검증을 완료하세요:

1. `prepare_tomorrow.py` 실행
2. 생성된 `watchlist_YYYYMMDD.json` 파일 확인
3. `latest_watchlist.json` 연결 (아래 참고)







