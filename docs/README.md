# 프로젝트 문서 인덱스

## 📋 문서 구조

이 프로젝트의 모든 문서는 다음 구조로 관리됩니다:

```
docs/
├── README.md                    # 이 파일 (문서 인덱스)
├── governance.md                # 문서 거버넌스 가이드
├── DOCUMENT_STATUS.md           # 문서 현황 및 상태 관리
├── gatekeeper/                  # 문지기봇 문서
│   ├── CHANGELOG.md            # 변경 이력
│   ├── DESIGN_REVIEW.md        # 설계 검토 결과
│   ├── DESIGN_INTENT_REFLECTION.md  # 설계 의도 코드 반영
│   ├── IMPLEMENTATION_SUMMARY.md    # 구현 완료 요약
│   ├── SECONDARY_FILTER_IMPLEMENTATION.md  # 2차 필터 구현
│   ├── COMPLIANCE_CHECK.md     # 구현 완료 기준 검증
│   ├── ROLE_COMPLIANCE_AUDIT.md  # 역할 및 범위 검증
│   ├── OUTPUT_CONTRACT.md      # 출력 데이터 계약
│   ├── OUTPUT_FORMAT_VERIFICATION.md  # 출력 형식 검증
│   ├── WATCHLIST_FORMAT_SPEC.md  # Watchlist 형식 명세
│   └── INPUT_FORMAT.md         # 입력 포맷 설명
├── scout/                       # 정찰봇 문서
│   └── ANALYZER_SCHEMA.md       # 분석 결과 스키마
├── experiments/                 # 실험/메모 문서
│   ├── AUTO_TRADING_ROADMAP.md  # 자동매매 로드맵
│   └── ML_FEATURE_DESIGN.md     # 딥러닝 Feature 설계
└── _ARCHIVE/                    # 아카이브 문서
    └── FORMATTING_GUIDE.md      # 포맷팅 가이드 (더 이상 사용 안 함)
```

---

## 🗂️ 문서 카테고리

### 1. 프로젝트 개요
- **[README.md](../README.md)**: 프로젝트 메인 README
- **[AUTO_TRADING_ROADMAP.md](./experiments/AUTO_TRADING_ROADMAP.md)**: 자동매매 로드맵 (실험 문서)

### 2. 문지기봇 (Gatekeeper Bot) - 공식 문서

**위치**: `docs/gatekeeper/`

#### 📐 설계 문서 (Design)
- **[DESIGN_REVIEW.md](./gatekeeper/DESIGN_REVIEW.md)**: 설계 검토 결과
- **[DESIGN_INTENT_REFLECTION.md](./gatekeeper/DESIGN_INTENT_REFLECTION.md)**: 설계 의도 코드 반영

#### 🔨 구현 문서 (Implementation)
- **[IMPLEMENTATION_SUMMARY.md](./gatekeeper/IMPLEMENTATION_SUMMARY.md)**: 구현 완료 요약
- **[SECONDARY_FILTER_IMPLEMENTATION.md](./gatekeeper/SECONDARY_FILTER_IMPLEMENTATION.md)**: 2차 필터 구현

#### ✅ 검증 문서 (Compliance)
- **[COMPLIANCE_CHECK.md](./gatekeeper/COMPLIANCE_CHECK.md)**: 구현 완료 기준 검증
- **[ROLE_COMPLIANCE_AUDIT.md](./gatekeeper/ROLE_COMPLIANCE_AUDIT.md)**: 역할 및 범위 위반 여부 검증
- **[OUTPUT_FORMAT_VERIFICATION.md](./gatekeeper/OUTPUT_FORMAT_VERIFICATION.md)**: 출력 형식 검증

#### 📋 계약 문서 (Contract/Spec)
- **[OUTPUT_CONTRACT.md](./gatekeeper/OUTPUT_CONTRACT.md)**: 출력 데이터 계약
- **[WATCHLIST_FORMAT_SPEC.md](./gatekeeper/WATCHLIST_FORMAT_SPEC.md)**: Watchlist 형식 명세 ⭐ 공식 명세
- **[INPUT_FORMAT.md](./gatekeeper/INPUT_FORMAT.md)**: 입력 포맷 설명

#### 📝 변경 이력
- **[CHANGELOG.md](./gatekeeper/CHANGELOG.md)**: 변경 이력

### 3. 정찰봇 (Scout Bot)

**위치**: `docs/scout/`

- **[ANALYZER_SCHEMA.md](./scout/ANALYZER_SCHEMA.md)**: 분석 결과 스키마

### 4. 실험/메모 문서

**위치**: `docs/experiments/`

- **[AUTO_TRADING_ROADMAP.md](./experiments/AUTO_TRADING_ROADMAP.md)**: 자동매매 로드맵
- **[ML_FEATURE_DESIGN.md](./experiments/ML_FEATURE_DESIGN.md)**: 딥러닝 Feature 설계

### 5. 아카이브 문서

**위치**: `docs/_ARCHIVE/`

- **[FORMATTING_GUIDE.md](./_ARCHIVE/FORMATTING_GUIDE.md)**: 포맷팅 가이드 (더 이상 사용 안 함)

---

## 📖 문서 읽기 가이드

### 처음 시작하는 경우
1. [프로젝트 README.md](../README.md) - 프로젝트 개요
2. [문지기봇 출력 계약](./gatekeeper/OUTPUT_CONTRACT.md) - 출력 데이터 계약
3. [Watchlist 형식 명세](./gatekeeper/WATCHLIST_FORMAT_SPEC.md) - 공식 출력 형식

### 문지기봇 개발자
1. [설계 검토](./gatekeeper/DESIGN_REVIEW.md) - 설계 검토
2. [구현 요약](./gatekeeper/IMPLEMENTATION_SUMMARY.md) - 구현 요약
3. [출력 계약](./gatekeeper/OUTPUT_CONTRACT.md) - 출력 계약
4. [Watchlist 형식 명세](./gatekeeper/WATCHLIST_FORMAT_SPEC.md) - 공식 명세

### 정찰봇 개발자
1. [프로젝트 README.md](../README.md) - 정찰봇 섹션
2. [분석 스키마](./scout/ANALYZER_SCHEMA.md) - 분석 스키마

### 운영자
1. [Watchlist 형식 명세](./gatekeeper/WATCHLIST_FORMAT_SPEC.md) - Watchlist 형식
2. [입력 포맷](./gatekeeper/INPUT_FORMAT.md) - 입력 포맷

---

## 🔍 공식 문서 표시

### ⭐ 공식 명세 문서 (Spec)
- **[WATCHLIST_FORMAT_SPEC.md](./gatekeeper/WATCHLIST_FORMAT_SPEC.md)**: 문지기봇 출력 형식 공식 명세
- **[INPUT_FORMAT.md](./gatekeeper/INPUT_FORMAT.md)**: 문지기봇 입력 형식 공식 명세
- **[ANALYZER_SCHEMA.md](./scout/ANALYZER_SCHEMA.md)**: 분석 결과 스키마 공식 명세

### 📐 설계 문서 (Design)
- **[DESIGN_REVIEW.md](./gatekeeper/DESIGN_REVIEW.md)**: 설계 검토 결과
- **[DESIGN_INTENT_REFLECTION.md](./gatekeeper/DESIGN_INTENT_REFLECTION.md)**: 설계 의도 코드 반영

### 📋 계약 문서 (Contract)
- **[OUTPUT_CONTRACT.md](./gatekeeper/OUTPUT_CONTRACT.md)**: 출력 데이터 계약

---

## 🔍 문서 검색

### 키워드별 검색

**설계 관련**: `DESIGN`, `DESIGN_REVIEW`, `DESIGN_INTENT`
**구현 관련**: `IMPLEMENTATION`, `SECONDARY_FILTER`
**검증 관련**: `COMPLIANCE`, `AUDIT`, `VERIFICATION`
**계약 관련**: `CONTRACT`, `FORMAT`, `SPEC`
**입력/출력**: `INPUT`, `OUTPUT`, `WATCHLIST`

---

## 📝 문서 작성 가이드

문서 작성 시 다음 가이드를 따르세요:
- [governance.md](./governance.md) - 문서 거버넌스 가이드

---

## 🔄 문서 업데이트

문서는 다음 경우에 업데이트됩니다:
- 새로운 기능 추가 시
- 설계 변경 시
- 버그 수정 시
- 검증 완료 시

업데이트 시 [governance.md](./governance.md)의 규칙을 따르세요.

---

## 📊 문서 현황

문서 현황은 [DOCUMENT_STATUS.md](./DOCUMENT_STATUS.md)에서 확인할 수 있습니다.

