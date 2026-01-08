# 정찰봇 (Scout Bot) 문서

## 📋 개요

정찰봇은 장 중 상시 실행 프로세스로서 문지기봇이 선정한 종목을 감시·기록하는 봇입니다.

**위치**: `test/scout_bot/`

---

## 📚 문서 목록

### 메인 문서
- **[프로젝트 README.md](../../README.md)**: 정찰봇 섹션 참조

### 분석기 문서
- **[test/framework/analyzer/schema.md](../../test/framework/analyzer/schema.md)**: 분석 결과 스키마

---

## 🔍 빠른 참조

### 주요 기능
- Watchlist 종목 감시 (2분 간격)
- Observer 패턴 감지 (Volume, BaseCandle, Box)
- 실시간 관찰 결과 기록 (JSONL 형식)

### 주요 파일
- `test/scout_bot/day_main.py`: 정찰봇 메인
- `test/framework/engine/runner.py`: 정찰 엔진
- `test/framework/observer/`: 패턴 감지 모듈

### 기록 위치
- `records/scout/YYYY-MM-DD/{종목코드}.jsonl`

### 텔레그램 명령어
- `/add 종목코드`: 종목 추가
- `/remove 종목코드`: 종목 제거
- `/list`: 현재 watchlist 확인
- `/status`: 상태 확인

---

## 📝 문서 업데이트

문서는 다음 경우에 업데이트됩니다:
- 새로운 Observer 패턴 추가 시
- 기록 형식 변경 시
- 텔레그램 명령어 추가 시

업데이트 시 [문서 거버넌스 가이드](../governance.md)를 따르세요.


