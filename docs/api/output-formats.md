# API 출력 형식 문서

## 📋 개요

프로젝트 내 모든 모듈의 출력 형식을 통합 관리하는 문서입니다.

---

## 📚 출력 형식 목록

### 1. 문지기봇 출력

**파일**: `scout_selector/output/watchlist_YYYYMMDD.json`

**문서**:
- [문지기봇 출력 계약](../../scout_selector/OUTPUT_CONTRACT.md)
- [Watchlist 형식 명세](../../scout_selector/output/WATCHLIST_FORMAT_SPEC.md)
- [Watchlist 형식 예시](../../scout_selector/output/WATCHLIST_FORMAT_EXAMPLE.json)

**주요 필드**:
- `meta.gatekeeper_version`: 문지기봇 버전
- `category`: 카테고리 (largecap/volume/structure/theme)
- `selection_reason`: 선정 사유 요약
- `structure_score`: 구조 점수 (구조형만, 0~100점)
- `indicators`: 주요 지표 값

---

### 2. 정찰봇 출력

**파일**: `records/scout/YYYY-MM-DD/{종목코드}.jsonl`

**문서**:
- [프로젝트 README.md](../../README.md) - 정찰봇 섹션

**주요 필드**:
- `meta.date`: 기록 날짜
- `snapshot`: 실시간 스냅샷
- `observer`: Observer 트리거 정보
- `base_candle`: 기준봉 정보
- `box`: 박스 형성 정보

---

### 3. 분석기 출력

**파일**: `records/analysis/YYYY-MM-DD/daily_analysis.{json,txt}`

**문서**:
- [분석 결과 스키마](../../test/framework/analyzer/schema.md)

**주요 필드**:
- `date`: 분석 날짜
- `market_character`: 시장 성격
- `observer_stats`: Observer 통계
- `box_stats`: Box 통계

---

## 🔄 출력 형식 변경 프로세스

1. **변경 제안**: 이슈 트래커에 변경 제안
2. **문서 업데이트**: 관련 문서 업데이트
3. **코드 구현**: 코드 변경
4. **검증**: 출력 형식 검증
5. **승인**: 변경 승인 및 배포

---

## 📝 참고

각 모듈의 상세 출력 형식은 해당 모듈 문서를 참조하세요.






