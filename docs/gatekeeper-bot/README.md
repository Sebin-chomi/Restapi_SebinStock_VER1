# 문지기봇 (Gatekeeper Bot) 문서

## 📋 개요

문지기봇은 장 마감 후 배치 프로세스로 실행되어 전 종목을 대상으로 입구 필터 및 1·2차 필터링을 수행하여 정찰봇이 감시할 종목 후보군을 생성하는 독립 실행 봇입니다.

**위치**: `scout_selector/`

---

## 📚 문서 목록

### 설계 문서

- **[DESIGN_REVIEW.md](../../scout_selector/DESIGN_REVIEW.md)**: 설계 검토 결과
  - 현재 구현 vs 설계 비교
  - 불일치 사항 및 개선 방향

- **[DESIGN_INTENT_REFLECTION.md](../../scout_selector/DESIGN_INTENT_REFLECTION.md)**: 설계 의도 코드 반영
  - 코드 구조에 설계 의도 명시적 반영
  - 3단계 필터 구분 (Gate/Primary/Secondary)

### 구현 문서

- **[IMPLEMENTATION_SUMMARY.md](../../scout_selector/IMPLEMENTATION_SUMMARY.md)**: 구현 완료 요약
  - 입구 필터 (Gate Filter) 구현
  - 1차 필터 (Primary Filter) 구현
  - 일중 변동성 계산 개선

- **[SECONDARY_FILTER_IMPLEMENTATION.md](../../scout_selector/SECONDARY_FILTER_IMPLEMENTATION.md)**: 2차 필터 구현
  - 구조형 점수 체계 (0~100점)
  - 구조형 후보 유지 기준
  - 최종 후보군 압축

### 검증 문서

- **[COMPLIANCE_CHECK.md](../../scout_selector/COMPLIANCE_CHECK.md)**: 구현 완료 기준 검증
  - 출력 데이터 계약 준수 확인
  - 명시적 금지 사항 준수 확인
  - 구현 완료 기준 충족 확인

- **[ROLE_COMPLIANCE_AUDIT.md](../../scout_selector/ROLE_COMPLIANCE_AUDIT.md)**: 역할 및 범위 위반 여부 검증
  - 종목 선별 외의 역할 수행 여부
  - 매수/매도 판단, 포지션 관리, 계좌 접근 코드 존재 여부
  - 장 중 재선정 또는 실시간 이벤트 의존 로직 존재 여부

- **[OUTPUT_FORMAT_VERIFICATION.md](../../scout_selector/OUTPUT_FORMAT_VERIFICATION.md)**: 출력 형식 검증
  - 코드 검증 결과
  - 최신 형식 필드 체크리스트

### 계약 문서

- **[OUTPUT_CONTRACT.md](../../scout_selector/OUTPUT_CONTRACT.md)**: 출력 데이터 계약
  - 출력 형식 명세
  - 필수 필드 정의
  - 명시적 금지 사항
  - 구현 완료 기준

- **[output/WATCHLIST_FORMAT_SPEC.md](../../scout_selector/output/WATCHLIST_FORMAT_SPEC.md)**: Watchlist 형식 명세
  - JSON 구조 상세 설명
  - 각 카테고리별 필드 설명
  - 정찰봇 연동 방법

- **[output/WATCHLIST_FORMAT_EXAMPLE.json](../../scout_selector/output/WATCHLIST_FORMAT_EXAMPLE.json)**: Watchlist 형식 예시
  - 실제 JSON 예시 파일

### 입력 문서

- **[input/README.md](../../scout_selector/input/README.md)**: 입력 포맷 설명
  - 조건식 입력 포맷
  - 뉴스 입력 포맷
  - 히스토리 관리

---

## 🗺️ 문서 읽기 순서

### 처음 시작하는 경우
1. [OUTPUT_CONTRACT.md](../../scout_selector/OUTPUT_CONTRACT.md) - 출력 데이터 계약
2. [DESIGN_REVIEW.md](../../scout_selector/DESIGN_REVIEW.md) - 설계 검토
3. [IMPLEMENTATION_SUMMARY.md](../../scout_selector/IMPLEMENTATION_SUMMARY.md) - 구현 요약

### 개발자
1. [DESIGN_INTENT_REFLECTION.md](../../scout_selector/DESIGN_INTENT_REFLECTION.md) - 설계 의도 코드 반영
2. [SECONDARY_FILTER_IMPLEMENTATION.md](../../scout_selector/SECONDARY_FILTER_IMPLEMENTATION.md) - 2차 필터 구현
3. [input/README.md](../../scout_selector/input/README.md) - 입력 포맷

### 검증자
1. [COMPLIANCE_CHECK.md](../../scout_selector/COMPLIANCE_CHECK.md) - 구현 완료 기준 검증
2. [ROLE_COMPLIANCE_AUDIT.md](../../scout_selector/ROLE_COMPLIANCE_AUDIT.md) - 역할 및 범위 검증
3. [OUTPUT_FORMAT_VERIFICATION.md](../../scout_selector/OUTPUT_FORMAT_VERIFICATION.md) - 출력 형식 검증

### 운영자
1. [output/WATCHLIST_FORMAT_SPEC.md](../../scout_selector/output/WATCHLIST_FORMAT_SPEC.md) - Watchlist 형식 명세
2. [output/WATCHLIST_FORMAT_EXAMPLE.json](../../scout_selector/output/WATCHLIST_FORMAT_EXAMPLE.json) - 형식 예시

---

## 🔍 빠른 참조

### 핵심 개념
- **Gate Filter**: 입구 필터 (거래량=0, 거래대금<25억 제거)
- **Primary Filter**: 1차 필터 (OR 조건: 거래량 스파이크>=1.8 OR 거래대금>=50억 OR 변동성>=3.0%)
- **Secondary Filter**: 2차 필터 (버킷별 점수 계산 및 선정)
- **Structure Score**: 구조 점수 (0~100점, 구조형만)

### 주요 파일
- `selector.py`: 문지기봇 핵심 엔진
- `runner.py`: 오늘 종목 선정
- `prepare_tomorrow.py`: 내일 종목 선정 (정찰봇이 사용)
- `manual_select.py`: 수동 종목 선정

### 출력 파일
- `output/watchlist_YYYYMMDD.json`: 날짜별 watchlist (정찰봇이 읽음)
- `output/latest_watchlist.json`: 최신 watchlist (운영 편의용)

---

## 📝 문서 업데이트

문서는 다음 경우에 업데이트됩니다:
- 새로운 필터 단계 추가 시
- 출력 형식 변경 시
- 검증 완료 시
- 설계 변경 시

업데이트 시 [문서 거버넌스 가이드](../governance.md)를 따르세요.






