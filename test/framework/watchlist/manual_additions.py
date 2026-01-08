# ===============================
# test/framework/watchlist/manual_additions.py
# 텔레그램 수동 추가 종목 영속 저장
# ===============================
"""
수동 추가 종목 관리 모듈

역할:
- 텔레그램 /add 명령으로 추가된 종목을 날짜별로 영속 저장
- 문지기봇 산출물과 명확히 분리된 운영 레이어
- watchlist_YYYYMMDD.json은 절대 수정하지 않음
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set, Optional


# =========================
# Paths
# =========================

def get_manual_additions_file(date: Optional[str] = None) -> Path:
    """
    수동 추가 파일 경로 반환
    
    Args:
        date: 날짜 (YYYYMMDD, None이면 오늘)
        
    Returns:
        파일 경로
    """
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    
    # 프로젝트 루트 기준으로 scout_selector/output 경로 찾기
    current_file = Path(__file__).resolve()
    # test/framework/watchlist/manual_additions.py → 프로젝트 루트
    project_root = current_file.parents[3]
    output_dir = project_root / "scout_selector" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    return output_dir / f"manual_additions_{date}.json"


# =========================
# Load / Save
# =========================

def load_manual_additions(date: Optional[str] = None) -> Dict:
    """
    수동 추가 종목 파일 로드
    
    Args:
        date: 날짜 (YYYYMMDD, None이면 오늘)
        
    Returns:
        수동 추가 데이터 딕셔너리 (파일 없으면 빈 구조)
    """
    file_path = get_manual_additions_file(date)
    
    if not file_path.exists():
        return {
            "date": date or datetime.now().strftime("%Y%m%d"),
            "updated_at": None,
            "source": "telegram",
            "symbols": [],
        }
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"[WARN] manual_additions JSON 로드 실패: {file_path} - {e}")
        return {
            "date": date or datetime.now().strftime("%Y%m%d"),
            "updated_at": None,
            "source": "telegram",
            "symbols": [],
        }


def save_manual_additions(data: Dict, date: Optional[str] = None) -> bool:
    """
    수동 추가 종목 파일 저장
    
    Args:
        data: 저장할 데이터 딕셔너리
        date: 날짜 (YYYYMMDD, None이면 오늘)
        
    Returns:
        성공 여부
    """
    file_path = get_manual_additions_file(date)
    
    try:
        # updated_at 갱신
        data["updated_at"] = datetime.now().isoformat()
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"[ERROR] manual_additions JSON 저장 실패: {file_path} - {e}")
        return False


# =========================
# Add / Remove
# =========================

def add_manual_symbol(symbol: str, date: Optional[str] = None, reason: str = "/add command") -> bool:
    """
    수동 추가 종목 추가
    
    Args:
        symbol: 종목 코드
        date: 날짜 (YYYYMMDD, None이면 오늘)
        reason: 추가 사유
        
    Returns:
        성공 여부 (이미 존재하면 False)
    """
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    
    # 기존 데이터 로드
    data = load_manual_additions(date)
    data["date"] = date  # 날짜 보장
    
    # 기존 symbols 추출
    existing_symbols = {item["symbol"] for item in data.get("symbols", [])}
    
    # 중복 체크
    if symbol in existing_symbols:
        return False  # 이미 존재
    
    # 신규 symbol 추가
    new_item = {
        "symbol": symbol,
        "added_by": "telegram",
        "added_at": datetime.now().isoformat(),
        "reason": reason,
    }
    
    data.setdefault("symbols", []).append(new_item)
    
    # 파일 저장
    return save_manual_additions(data, date)


def remove_manual_symbol(symbol: str, date: Optional[str] = None) -> bool:
    """
    수동 추가 종목 제거
    
    Args:
        symbol: 종목 코드
        date: 날짜 (YYYYMMDD, None이면 오늘)
        
    Returns:
        성공 여부 (존재하지 않으면 False)
    """
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    
    # 기존 데이터 로드
    data = load_manual_additions(date)
    data["date"] = date  # 날짜 보장
    
    # symbols에서 제거
    symbols = data.get("symbols", [])
    original_count = len(symbols)
    
    data["symbols"] = [item for item in symbols if item["symbol"] != symbol]
    
    # 변경사항이 없으면 False
    if len(data["symbols"]) == original_count:
        return False
    
    # 파일 저장
    return save_manual_additions(data, date)


def get_manual_symbols(date: Optional[str] = None) -> List[str]:
    """
    수동 추가 종목 코드 리스트 반환
    (모든 날짜의 manual_additions 파일을 스캔하여 누적)
    
    Args:
        date: 날짜 (사용하지 않음, 모든 파일 스캔)
        
    Returns:
        종목 코드 리스트 (중복 제거)
    """
    # 모든 manual_additions 파일 스캔
    output_dir = get_manual_additions_file().parent
    
    all_symbols = set()
    
    # manual_additions_*.json 파일 모두 찾기
    for file_path in output_dir.glob("manual_additions_*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data.get("symbols", []):
                    symbol = item.get("symbol") if isinstance(item, dict) else item
                    if symbol:
                        all_symbols.add(str(symbol).zfill(6))  # 6자리로 정규화
        except Exception as e:
            print(f"[WARN] manual_additions 파일 로드 실패: {file_path} - {e}")
            continue
    
    return sorted(list(all_symbols))


