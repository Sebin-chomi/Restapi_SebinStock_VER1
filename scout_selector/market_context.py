# ===============================
# 종목선정회의 (MarketContext) v0
# ===============================
"""
종목선정회의 모듈

역할:
- 종목 선정 전에 시스템이 공유하는 '판단의 전제'를 기록
- 시장 인식 상태, 관찰 기준, 배제 기준, 자유 메모 기록
- 종목 선택/추천/예측은 하지 않음 (기록만)

설계 원칙:
- 사람이 아무것도 입력하지 못한 날도 자동 생성되어야 함
- 기본값만 있어도 정상 상태
- 문지기봇은 MarketContext 없어도 정상 동작해야 함
"""
from __future__ import annotations

import json
import sys
import io
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Windows 콘솔 인코딩 설정
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 프로젝트 루트를 Python 경로에 추가
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# =========================
# Constants
# =========================

MODULE_NAME = "종목선정회의"
MODULE_NAME_EN = "MarketContext"
CONTEXT_VERSION = "v0"

# 기본값
DEFAULT_MARKET_STATUS = "unknown"
DEFAULT_SELECTION_BASIS = []
DEFAULT_EXCLUSION_BASIS = []
DEFAULT_NOTES = "관찰 데이터 수집 단계"

# =========================
# Paths
# =========================

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =========================
# MarketContext 생성
# =========================

def create_default_context(date: str) -> Dict[str, Any]:
    """
    기본값 MarketContext 생성
    
    Args:
        date: 거래일 (YYYYMMDD)
        
    Returns:
        MarketContext 딕셔너리 (기본값)
    """
    return {
        "date": date,
        "context_level": CONTEXT_VERSION,
        "market_status": DEFAULT_MARKET_STATUS,
        "selection_basis": DEFAULT_SELECTION_BASIS.copy(),
        "exclusion_basis": DEFAULT_EXCLUSION_BASIS.copy(),
        "notes": DEFAULT_NOTES,
        "created_at": datetime.now().isoformat(),
    }


def create_context(
    date: str,
    market_status: Optional[str] = None,
    selection_basis: Optional[List[str]] = None,
    exclusion_basis: Optional[List[str]] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """
    MarketContext 생성 (사용자 입력 또는 기본값)
    
    Args:
        date: 거래일 (YYYYMMDD)
        market_status: 시장 상태 ("unknown" | "observed", None이면 기본값)
        selection_basis: 관찰 기준 리스트 (None이면 기본값)
        exclusion_basis: 배제 기준 리스트 (None이면 기본값)
        notes: 자유 메모 (None이면 기본값)
        
    Returns:
        MarketContext 딕셔너리
    """
    context = create_default_context(date)
    
    # 사용자 입력이 있으면 덮어쓰기
    if market_status is not None:
        if market_status in ["unknown", "observed"]:
            context["market_status"] = market_status
        else:
            print(f"⚠️  잘못된 market_status: {market_status} (unknown 또는 observed만 허용)")
    
    if selection_basis is not None:
        context["selection_basis"] = selection_basis if isinstance(selection_basis, list) else []
    
    if exclusion_basis is not None:
        context["exclusion_basis"] = exclusion_basis if isinstance(exclusion_basis, list) else []
    
    if notes is not None:
        context["notes"] = notes
    
    return context


# =========================
# 파일 저장/조회
# =========================

def get_context_file_path(date: str) -> Path:
    """
    MarketContext 파일 경로 반환
    
    Args:
        date: 거래일 (YYYYMMDD)
        
    Returns:
        파일 경로
    """
    return OUTPUT_DIR / f"market_context_{date}.json"


def save_context(context: Dict[str, Any], date: Optional[str] = None) -> bool:
    """
    MarketContext 파일 저장
    
    Args:
        context: MarketContext 딕셔너리
        date: 거래일 (YYYYMMDD, None이면 context에서 추출)
        
    Returns:
        성공 여부
    """
    if date is None:
        date = context.get("date")
        if not date:
            print("❌ date가 없어 파일을 저장할 수 없습니다.")
            return False
    
    file_path = get_context_file_path(date)
    
    try:
        # updated_at 갱신
        context["updated_at"] = datetime.now().isoformat()
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(context, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"❌ MarketContext 저장 실패: {file_path} - {e}")
        return False


def load_context(date: str) -> Optional[Dict[str, Any]]:
    """
    MarketContext 파일 로드
    
    Args:
        date: 거래일 (YYYYMMDD)
        
    Returns:
        MarketContext 딕셔너리 (파일 없으면 None)
    """
    file_path = get_context_file_path(date)
    
    if not file_path.exists():
        return None
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            context = json.load(f)
        return context
    except Exception as e:
        print(f"⚠️  MarketContext 로드 실패: {file_path} - {e}")
        return None


def get_or_create_context(date: str) -> Dict[str, Any]:
    """
    MarketContext 조회 또는 기본값 생성
    
    파일이 없으면 기본값으로 생성하여 반환 (파일 저장은 하지 않음)
    
    Args:
        date: 거래일 (YYYYMMDD)
        
    Returns:
        MarketContext 딕셔너리 (항상 반환)
    """
    context = load_context(date)
    
    if context is None:
        # 파일이 없으면 기본값 생성 (저장은 하지 않음)
        context = create_default_context(date)
    
    return context


# =========================
# 자동 생성 (파이프라인 통합용)
# =========================

def ensure_context_exists(date: str) -> Dict[str, Any]:
    """
    MarketContext 파일이 존재하는지 확인하고, 없으면 기본값으로 생성
    
    파이프라인에서 자동 호출용
    
    Args:
        date: 거래일 (YYYYMMDD)
        
    Returns:
        MarketContext 딕셔너리
    """
    context = load_context(date)
    
    if context is None:
        # 파일이 없으면 기본값으로 생성하여 저장
        print(f"📝 {MODULE_NAME} 파일 없음 → 기본값으로 자동 생성")
        context = create_default_context(date)
        save_context(context, date)
        print(f"   저장 완료: market_context_{date}.json")
    else:
        print(f"✅ {MODULE_NAME} 파일 존재: market_context_{date}.json")
    
    return context


# =========================
# CLI (선택적 - 수동 입력용)
# =========================

def main():
    """MarketContext 수동 생성/수정 CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description=f"{MODULE_NAME} ({MODULE_NAME_EN}) - 시장 컨텍스트 기록")
    parser.add_argument(
        "--date",
        type=str,
        help="거래일 (YYYYMMDD, 기본값: 오늘)",
        default=None,
    )
    parser.add_argument(
        "--market-status",
        type=str,
        choices=["unknown", "observed"],
        help="시장 상태",
        default=None,
    )
    parser.add_argument(
        "--selection-basis",
        type=str,
        nargs="+",
        help="관찰 기준 (여러 개 가능)",
        default=None,
    )
    parser.add_argument(
        "--exclusion-basis",
        type=str,
        nargs="+",
        help="배제 기준 (여러 개 가능)",
        default=None,
    )
    parser.add_argument(
        "--notes",
        type=str,
        help="자유 메모",
        default=None,
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="기본값으로 자동 생성 (입력 없이)",
    )
    
    args = parser.parse_args()
    
    # 날짜 결정
    if args.date:
        date = args.date
    else:
        date = datetime.now().strftime("%Y%m%d")
    
    print("=" * 60)
    print(f"📋 {MODULE_NAME} ({MODULE_NAME_EN})")
    print("=" * 60)
    print(f"\n📅 날짜: {date}")
    
    # 자동 생성 모드
    if args.auto:
        context = ensure_context_exists(date)
        print(f"\n✅ 기본값으로 자동 생성 완료")
    else:
        # 사용자 입력 또는 기본값
        context = create_context(
            date=date,
            market_status=args.market_status,
            selection_basis=args.selection_basis,
            exclusion_basis=args.exclusion_basis,
            notes=args.notes,
        )
        
        # 저장
        if save_context(context, date):
            print(f"\n✅ 저장 완료: market_context_{date}.json")
        else:
            print(f"\n❌ 저장 실패")
            sys.exit(1)
    
    # 출력
    print(f"\n📄 MarketContext 내용:")
    print(f"   market_status: {context['market_status']}")
    print(f"   selection_basis: {context['selection_basis']}")
    print(f"   exclusion_basis: {context['exclusion_basis']}")
    print(f"   notes: {context['notes']}")
    print("=" * 60)


if __name__ == "__main__":
    main()


