# 신호 수집기 (Signals Collector) 문서

## 📋 개요

신호 수집기는 외부 신호(조건식·뉴스)를 수집하여 문지기봇이 사용할 수 있는 표준 형식으로 변환하는 모듈입니다.

**위치**: `signals_collector/`

---

## 📚 문서 목록

### 메인 문서
- **[signals_collector/README.md](../../signals_collector/README.md)**: 신호 수집기 문서

### 관련 문서
- **[문지기봇 입력 포맷](../../scout_selector/input/README.md)**: 입력 포맷 설명

---

## 🔍 빠른 참조

### 주요 기능
- 조건식 수집 (Kiwoom API)
- 뉴스 수집 (Naver News RSS)
- 키워드 자동 추출
- Telegram 알림

### 주요 파일
- `signals_collector/run_collect.py`: 메인 실행 스크립트
- `signals_collector/collectors/condition_kiwoom.py`: 조건식 수집기
- `signals_collector/collectors/news_provider.py`: 뉴스 수집기

### 출력 위치
- `scout_selector/input/conditions/conditions_YYYYMMDD.json`
- `scout_selector/input/news/news_YYYYMMDD.json`

---

## 📝 문서 업데이트

문서는 다음 경우에 업데이트됩니다:
- 새로운 수집기 추가 시
- 출력 형식 변경 시
- API 연동 변경 시

업데이트 시 [문서 거버넌스 가이드](../governance.md)를 따르세요.


