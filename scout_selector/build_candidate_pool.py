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
from typing import Dict, List, Set, Optional

# Windows 콘솔 인코딩 설정
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

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

OUTPUT_DIR.mkdir(exist_ok=True)


# =========================
# Input Source Collectors
# =========================

def collect_turnover_top(date: str, top_n: int = DEFAULT_TURNOVER_TOP) -> Set[str]:
    """
    거래대금 상위 N 종목 수집
    
    Args:
        date: 날짜 (YYYYMMDD)
        top_n: 상위 N개
        
    Returns:
        종목 코드 set
    """
    symbols = set()
    
    try:
        # 방법 1: API나 외부 소스에서 가져오기 (추후 확장)
        # 예: pykrx, 키움 API 등
        pass
    except Exception as e:
        print(f"  ⚠️  거래대금 상위 수집 실패: {e}")
    
    # 방법 2: 파일에서 읽기 (추후 확장)
    # 예: data/turnover_top_YYYYMMDD.csv 등
    
    return symbols


def collect_volume_top(date: str, top_n: int = DEFAULT_VOLUME_TOP) -> Set[str]:
    """
    거래량 상위/급증 종목 수집
    
    Args:
        date: 날짜 (YYYYMMDD)
        top_n: 상위 N개
        
    Returns:
        종목 코드 set
    """
    symbols = set()
    
    try:
        # 방법 1: API나 외부 소스에서 가져오기 (추후 확장)
        pass
    except Exception as e:
        print(f"  ⚠️  거래량 상위 수집 실패: {e}")
    
    # 방법 2: 파일에서 읽기 (추후 확장)
    
    return symbols


def collect_condition_symbols(date: str) -> Set[str]:
    """
    조건식/시그널 결과 종목 수집
    
    Args:
        date: 날짜 (YYYYMMDD)
        
    Returns:
        종목 코드 set
    """
    symbols = set()
    
    try:
        # input/conditions/conditions_YYYYMMDD.json에서 읽기
        condition_file = INPUT_DIR / "conditions" / f"conditions_{date}.json"
        
        if condition_file.exists():
            with open(condition_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            for condition in data.get("conditions", []):
                for symbol in condition.get("symbols", []):
                    if symbol:
                        symbols.add(symbol)
                        
            print(f"  ✅ 조건식 종목: {len(symbols)}개")
        else:
            print(f"  ℹ️  조건식 파일 없음: {condition_file.name}")
            
    except Exception as e:
        print(f"  ⚠️  조건식 종목 수집 실패: {e}")
    
    return symbols


def collect_fixed_symbols() -> Set[str]:
    """
    고정 기준 종목 수집 (대형주 등)
    
    Returns:
        종목 코드 set
    """
    return set(FIXED_SYMBOLS)


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
    
    # 입력 소스별 수집
    print(f"\n📥 입력 소스 수집 중...")
    
    sources_count = {}
    all_symbols = set()
    
    # 1. 거래대금 상위
    print(f"\n1️⃣ 거래대금 상위 {DEFAULT_TURNOVER_TOP}개")
    turnover_symbols = collect_turnover_top(date, DEFAULT_TURNOVER_TOP)
    sources_count["turnover_top"] = len(turnover_symbols)
    all_symbols.update(turnover_symbols)
    print(f"   수집: {len(turnover_symbols)}개")
    
    # 2. 거래량 상위
    print(f"\n2️⃣ 거래량 상위 {DEFAULT_VOLUME_TOP}개")
    volume_symbols = collect_volume_top(date, DEFAULT_VOLUME_TOP)
    sources_count["volume_top"] = len(volume_symbols)
    all_symbols.update(volume_symbols)
    print(f"   수집: {len(volume_symbols)}개")
    
    # 3. 조건식 결과
    print(f"\n3️⃣ 조건식/시그널 결과")
    condition_symbols = collect_condition_symbols(date)
    sources_count["conditions"] = len(condition_symbols)
    all_symbols.update(condition_symbols)
    
    # 4. 고정 기준 종목
    print(f"\n4️⃣ 고정 기준 종목")
    fixed_symbols = collect_fixed_symbols()
    sources_count["fixed_symbols"] = len(fixed_symbols)
    all_symbols.update(fixed_symbols)
    print(f"   수집: {len(fixed_symbols)}개 ({', '.join(sorted(fixed_symbols))})")
    
    # 중복 제거 및 정렬 (재현성을 위해)
    candidate_symbols = sorted(list(all_symbols))
    
    # 최대 종목 수 제한 (옵션)
    if max_symbols and len(candidate_symbols) > max_symbols:
        print(f"\n⚠️  후보 풀 크기 제한: {len(candidate_symbols)} → {max_symbols}")
        # 우선순위: 고정 종목 > 조건식 > 거래대금 > 거래량
        priority_symbols = set()
        priority_symbols.update(fixed_symbols)
        priority_symbols.update(condition_symbols)
        priority_symbols.update(turnover_symbols)
        
        if len(priority_symbols) < max_symbols:
            remaining = max_symbols - len(priority_symbols)
            volume_priority = sorted(list(volume_symbols - priority_symbols))[:remaining]
            priority_symbols.update(volume_priority)
        
        candidate_symbols = sorted(list(priority_symbols))[:max_symbols]
    
    # 최소 후보 풀 보장 (모든 소스 실패 시)
    if not candidate_symbols:
        print(f"\n⚠️  모든 입력 소스 실패 → 최소 후보 풀 생성 (고정 종목만)")
        candidate_symbols = sorted(FIXED_SYMBOLS)
        sources_count = {
            "turnover_top": 0,
            "volume_top": 0,
            "conditions": 0,
            "fixed_symbols": len(candidate_symbols),
        }
    
    print(f"\n✅ 후보 풀 생성 완료")
    print(f"   총 종목 수: {len(candidate_symbols)}개")
    
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
    
    # 출력 파일 경로
    output_file = OUTPUT_DIR / f"candidate_pool_{date}.json"
    
    # 멱등성 체크 (기존 파일이 있으면 재생성하지 않음)
    if output_file.exists() and not args.force:
        print("=" * 60)
        print(f"ℹ️  출력 파일이 이미 존재합니다: {output_file.name}")
        print(f"   재생성하려면 --force 옵션을 사용하세요.")
        print("=" * 60)
        return
    
    # 후보 풀 생성
    try:
        output = build_candidate_pool(date, max_symbols=args.max_symbols)
        
        # 파일 저장
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"\n📁 저장 완료: {output_file}")
        print(f"   캔들기록봇이 이 파일을 입력으로 사용합니다.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        
        # 최소 후보 풀 생성 시도
        print(f"\n⚠️  최소 후보 풀 생성 시도...")
        try:
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
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(minimal_output, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 최소 후보 풀 저장 완료: {output_file}")
            print(f"   (고정 종목만 포함: {', '.join(FIXED_SYMBOLS)})")
            
        except Exception as e2:
            print(f"❌ 최소 후보 풀 생성도 실패: {e2}")
            sys.exit(1)


if __name__ == "__main__":
    main()

