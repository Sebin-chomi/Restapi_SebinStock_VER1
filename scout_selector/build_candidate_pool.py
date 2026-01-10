# ===============================
# 대기실장봇 (Waiting Room Manager Bot) v1
# Candidate Pool Builder
# ===============================
"""
대기실장봇 실행 스크립트

역할:
- 장 마감 후 배치 프로세스로 실행
- 전 종목 중 가벼운 기준으로 후보 종목 풀 생성
- 캔들기록봇이 사용할 candidate_pool_YYYYMMDD.json 생성

실행 시점:
- 장 마감 후 (15:35 이후)
- 외부 오케스트레이션(Windows Task Scheduler 등)에 의해 트리거

핵심 원칙:
- 빠르고 넓게 (Recall 우선)
- 입력 소스 일부 실패해도 전체가 죽지 않게 (부분 성공 허용)
- OHLCV 계산/분석 금지 (가벼운 지표만 사용)
"""
from __future__ import annotations

import argparse
import json
import sys
import io
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Windows 콘솔 인코딩 설정
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 프로젝트 루트를 Python 경로에 추가 (모듈 import를 위해)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# =========================
# Constants
# =========================

BOT_NAME = "대기실장봇"
BOT_VERSION = "1.0.0"

# 고정 기준 종목 (항상 포함)
FIXED_SYMBOLS = ["005930", "000660"]  # 삼성전자, SK하이닉스

# 기본 설정값
DEFAULT_TURNOVER_TOP = 300
DEFAULT_VOLUME_TOP = 200

# =========================
# Paths
# =========================

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
INPUT_DIR = BASE_DIR / "input"
HISTORY_DIR = OUTPUT_DIR / "history"

OUTPUT_DIR.mkdir(exist_ok=True)
HISTORY_DIR.mkdir(exist_ok=True)


# =========================
# Input Source Loaders (Stub Design)
# =========================

def load_fixed_symbols() -> List[str]:
    """
    항상 포함되어야 하는 기준 종목 반환
    
    Returns:
        고정 종목 코드 리스트 (예: ['005930', '000660'])
    
    실패 ❌ 없음
    최소 1개 이상 보장
    """
    return FIXED_SYMBOLS.copy()


def load_turnover_top(date: str, limit: Optional[int] = None) -> List[str]:
    """
    특정 날짜 기준 거래대금 상위 종목 반환
    
    현재 단계:
    - 구현 미완료
    - 반드시 빈 리스트 반환
    
    Args:
        date: 날짜 (YYYYMMDD)
        limit: 상위 N개 (현재 미사용)
        
    Returns:
        종목 코드 리스트 (현재는 빈 리스트)
    
    📌 주의
    - 예외 발생 ❌
    - 파일 없음 ❌
    - API 실패 ❌
    → 전부 빈 리스트로 흡수
    """
    # 스텁: 항상 빈 리스트 반환
    return []


def load_volume_top(date: str, limit: Optional[int] = None) -> List[str]:
    """
    특정 날짜 기준 거래량 상위 종목 반환
    
    현재 단계:
    - 구현 미완료
    - 반드시 빈 리스트 반환
    
    Args:
        date: 날짜 (YYYYMMDD)
        limit: 상위 N개 (현재 미사용)
        
    Returns:
        종목 코드 리스트 (현재는 빈 리스트)
    
    📌 주의
    - 예외 발생 ❌
    - 파일 없음 ❌
    - API 실패 ❌
    → 전부 빈 리스트로 흡수
    """
    # 스텁: 항상 빈 리스트 반환
    return []


def load_condition_results(date: str) -> List[str]:
    """
    조건식 결과 파일에서 종목 코드 로드
    
    파일 경로:
    scout_selector/input/conditions/conditions_YYYYMMDD.json
    
    파일이 없으면:
    - 오류 ❌
    - 빈 리스트 반환 ⭕
    
    Args:
        date: 날짜 (YYYYMMDD)
        
    Returns:
        종목 코드 리스트
    
    📌 여기서도 파일 없음 = 정상
    """
    symbols = []
    
    # 파일 경로
    condition_file = INPUT_DIR / "conditions" / f"conditions_{date}.json"
    
    # 파일이 없으면 빈 리스트 반환 (정상)
    if not condition_file.exists():
        return []
    
    # 파일 읽기 시도 (실패해도 빈 리스트 반환)
    try:
        with open(condition_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 조건식 결과에서 종목 코드 추출
        for condition in data.get("conditions", []):
            for symbol in condition.get("symbols", []):
                if symbol:
                    symbols.append(str(symbol).zfill(6))  # 6자리 정규화
        
        # 중복 제거
        symbols = sorted(list(set(symbols)))
        
    except Exception:
        # 모든 예외는 빈 리스트로 흡수
        pass
    
    return symbols


# =========================
# Candidate Pool Builder
# =========================

def build_candidate_pool(
    date: str,
    max_symbols: Optional[int] = None,
) -> Dict:
    """
    후보 풀 생성
    
    Args:
        date: 날짜 (YYYYMMDD)
        max_symbols: 최대 종목 수 (None이면 제한 없음)
        
    Returns:
        후보 풀 딕셔너리
    """
    print("=" * 60)
    print(f"📋 {BOT_NAME} - 후보 풀 생성")
    print("=" * 60)
    print(f"\n📅 날짜: {date}")
    
    # 입력 소스별 수집 (설계서 스텁 구조)
    print("\n📥 입력 소스 수집 중...")
    
    # 1. 고정 종목 로더
    fixed = load_fixed_symbols()
    print(f"INFO  Fixed symbols loaded: {len(fixed)}")
    
    # 2. 거래대금 상위 로더 (스텁)
    turnover = load_turnover_top(date, limit=DEFAULT_TURNOVER_TOP)
    print(f"INFO  Turnover top loaded: {len(turnover)}")
    
    # 3. 거래량 상위 로더 (스텁)
    volume = load_volume_top(date, limit=DEFAULT_VOLUME_TOP)
    print(f"INFO  Volume top loaded: {len(volume)}")
    
    # 4. 조건식 결과 로더 (스텁 + 파일 체크)
    conditions = load_condition_results(date)
    print(f"INFO  Condition results loaded: {len(conditions)}")
    
    # 중복 제거 정책 (설계서 6장)
    all_symbols = fixed + turnover + volume + conditions
    candidate_symbols = sorted(list(set(all_symbols)))
    
    # sources 카운트 반영 규칙 (설계서 5장)
    # 함수 반환 기준으로만 집계 (중복 제거 전/후 상관 없음)
    sources_count = {
        "turnover_top": len(turnover),
        "volume_top": len(volume),
        "conditions": len(conditions),
        "fixed_symbols": len(fixed),
    }
    
    # 최소 후보 풀 보장 (모든 소스 실패 시)
    if not candidate_symbols:
        print("\n⚠️  모든 입력 소스 실패 → 최소 후보 풀 생성 (고정 종목만)")
        candidate_symbols = sorted(FIXED_SYMBOLS)
        sources_count = {
            "turnover_top": 0,
            "volume_top": 0,
            "conditions": 0,
            "fixed_symbols": len(candidate_symbols),
        }
    
    print("\n✅ 후보 풀 생성 완료")
    print(f"   총 종목 수: {len(candidate_symbols)}개")
    
    # 로깅 가이드 (설계서 7장)
    # WARN는 출력하되 종료 ❌
    auto_sources_sum = (
        sources_count.get("turnover_top", 0) +
        sources_count.get("volume_top", 0) +
        sources_count.get("conditions", 0)
    )
    if auto_sources_sum == 0:
        print(f"\n⚠️  WARN  No dynamic sources available for date={date}")
        print("   → 고정 종목만 포함됨 (정상 상태, 오류 아님)")
    
    # 출력 구조 생성
    created_at = datetime.now().isoformat()
    
    output = {
        "meta": {
            "date": date,
            "created_at": created_at,
            "bot_name": BOT_NAME,
            "bot_version": BOT_VERSION,
        },
        "sources": sources_count,
        "symbols": candidate_symbols,
    }
    
    return output


# =========================
# Main
# =========================

def main():
    parser = argparse.ArgumentParser(description=f"{BOT_NAME} - 후보 풀 생성")
    parser.add_argument(
        "--date",
        type=str,
        help="날짜 (YYYYMMDD, 기본값: 오늘)",
        default=None,
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="기존 파일이 있어도 재생성",
    )
    parser.add_argument(
        "--max-symbols",
        type=int,
        help="최대 종목 수 제한",
        default=None,
    )
    
    args = parser.parse_args()
    
    # 날짜 결정
    if args.date:
        date = args.date
    else:
        date = datetime.now().strftime("%Y%m%d")
    
    # 휴장일 체크
    from scout_selector.utils.market_calendar import is_market_open
    
    if not is_market_open(date):
        print("=" * 60)
        print(f"[INFO] Market closed on {date}")
        print(f"[SKIP] {BOT_NAME} - market closed")
        print("=" * 60)
        sys.exit(0)  # 정상 종료 (오류 아님)
    
    # history 디렉터리 경로 생성 (YYYY/MM 구조)
    year = date[:4]
    month = date[4:6]
    history_date_dir = HISTORY_DIR / year / month
    history_date_dir.mkdir(parents=True, exist_ok=True)
    
    # history 파일 경로 (immutable)
    history_file = history_date_dir / f"candidate_pool_{date}.json"
    
    # latest.json 경로 (운영 편의용)
    latest_file = OUTPUT_DIR / "latest.json"
    
    # 멱등성 체크: history 파일이 이미 존재하면 재생성하지 않음 (immutable 원칙)
    if history_file.exists() and not args.force:
        print("=" * 60)
        print(f"ℹ️  history 파일이 이미 존재합니다: {history_file}")
        print("   history는 불변(immutable)이므로 덮어쓰지 않습니다.")
        print("   재생성하려면 --force 옵션을 사용하세요.")
        print("=" * 60)
        
        # 기존 파일이 있으면 latest.json만 갱신 (선택적)
        # 백필 실행 시에는 latest.json을 갱신하지 않음 (오늘 날짜인 경우만)
        today_str = datetime.now().strftime("%Y%m%d")
        if date == today_str:
            try:
                import shutil
                shutil.copy2(str(history_file), str(latest_file))
                print("✅ latest.json 갱신 완료 (기존 파일 사용)")
            except Exception as e:
                print(f"⚠️  latest.json 갱신 실패: {e}")
        
        return
    
    # 후보 풀 생성
    try:
        output = build_candidate_pool(date, max_symbols=args.max_symbols)
        
        # 1. history 파일 저장 (immutable)
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"\n📁 history 저장 완료: {history_file}")
        
        # 2. 저장 성공 시 latest.json 갱신 (오늘 날짜인 경우만)
        today_str = datetime.now().strftime("%Y%m%d")
        if date == today_str:
            try:
                import shutil
                shutil.copy2(str(history_file), str(latest_file))
                print("✅ latest.json 갱신 완료")
            except Exception as e:
                print(f"⚠️  latest.json 갱신 실패: {e}")
                # latest 실패해도 history 저장은 성공했으므로 계속 진행
        else:
            print("ℹ️  백필 실행이므로 latest.json은 갱신하지 않습니다.")
        
        print("   캔들기록봇이 latest.json 또는 history 파일을 입력으로 사용합니다.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        
        # 최소 후보 풀 생성 시도
        print("\n⚠️  최소 후보 풀 생성 시도...")
        try:
            # history 디렉터리 경로 생성 (YYYY/MM 구조)
            year = date[:4]
            month = date[4:6]
            history_date_dir = HISTORY_DIR / year / month
            history_date_dir.mkdir(parents=True, exist_ok=True)
            
            history_file = history_date_dir / f"candidate_pool_{date}.json"
            latest_file = OUTPUT_DIR / "latest.json"
            
            minimal_output = {
                "meta": {
                    "date": date,
                    "created_at": datetime.now().isoformat(),
                    "bot_name": BOT_NAME,
                    "bot_version": BOT_VERSION,
                },
                "sources": {
                    "turnover_top": 0,
                    "volume_top": 0,
                    "conditions": 0,
                    "fixed_symbols": len(FIXED_SYMBOLS),
                },
                "symbols": sorted(FIXED_SYMBOLS),
            }
            
            # history 파일 저장
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(minimal_output, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 최소 후보 풀 저장 완료: {history_file}")
            print(f"   (고정 종목만 포함: {', '.join(FIXED_SYMBOLS)})")
            
            # latest.json 갱신 (오늘 날짜인 경우만)
            today_str = datetime.now().strftime("%Y%m%d")
            if date == today_str:
                try:
                    import shutil
                    shutil.copy2(str(history_file), str(latest_file))
                    print("✅ latest.json 갱신 완료")
                except Exception as e3:
                    print(f"⚠️  latest.json 갱신 실패: {e3}")
            
        except Exception as e2:
            print(f"❌ 최소 후보 풀 생성도 실패: {e2}")
            sys.exit(1)


if __name__ == "__main__":
    main()

