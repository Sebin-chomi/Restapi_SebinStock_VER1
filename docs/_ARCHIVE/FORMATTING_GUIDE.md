# 🔧 코드 자동 포맷팅 가이드

## 📋 VSCode에서 자동 포맷팅 설정

### 방법 1: Black 사용 (권장)

1. **Black 확장 설치**
   - VSCode 확장 마켓에서 "Black Formatter" 검색 후 설치

2. **설정 확인**
   - `.vscode/settings.json` 파일이 자동으로 생성됨
   - 저장 시 자동 포맷팅 활성화됨

3. **수동 포맷팅**
   - `Shift + Alt + F` (Windows/Linux)
   - `Shift + Option + F` (Mac)

### 방법 2: autopep8 사용

1. **autopep8 설치**
   ```bash
   pip install autopep8
   ```

2. **VSCode 설정**
   - `.vscode/settings.json`에서 autopep8 주석 해제

### 방법 3: 명령줄에서 사용

#### Black 사용
```bash
# 설치
pip install black

# 파일 포맷팅
black check_n_buy.py

# 전체 프로젝트 포맷팅
black .

# 미리보기 (변경사항만 확인)
black --diff check_n_buy.py
```

#### autopep8 사용
```bash
# 설치
pip install autopep8

# 파일 포맷팅
autopep8 --in-place --aggressive check_n_buy.py

# 전체 프로젝트 포맷팅
autopep8 --in-place --recursive --aggressive .
```

#### ruff 사용 (가장 빠름)
```bash
# 설치
pip install ruff

# 포맷팅
ruff format check_n_buy.py

# 전체 프로젝트
ruff format .
```

## 🎯 추천 설정

### Black (가장 인기)
- **장점**: 일관된 스타일, 빠름, 설정 간단
- **단점**: 매우 엄격함 (일부 개발자가 싫어함)

### autopep8
- **장점**: PEP 8 준수, 설정 가능
- **단점**: Black보다 느림

### ruff (최신)
- **장점**: 매우 빠름, 포맷팅 + 린팅 통합
- **단점**: 비교적 새로운 도구

## ⚙️ 현재 프로젝트 설정

`.vscode/settings.json` 파일이 생성되어 있으면:
- 저장 시 자동 포맷팅 활성화
- Black 포맷터 사용
- 최대 줄 길이: 100자

## 💡 팁

1. **저장 시 자동 포맷팅**: VSCode 설정에서 활성화됨
2. **수동 포맷팅**: `Shift + Alt + F`
3. **전체 프로젝트 포맷팅**: 터미널에서 `black .` 실행



