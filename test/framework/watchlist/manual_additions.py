# ===============================
# test/framework/watchlist/manual_additions.py
# 텔레그램 수동 추가 종목 영속 저장
# ===============================
"""
수동 추가 종목 관리 모듈

역할:
- 텔레그램 /add 명령으로 추가된 종목을 당일 한정으로 저장
- 사용자의 즉시 개입을 위한 당일 한정 감시 대상
- 장 마감 후 자동으로 제거됨
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
    수동 추가 파일 경로 반환 (날짜별)
    
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


def get_manual_additions_latest_file() -> Path:
    """
    수동 추가 최신 파일 경로 반환 (latest)
    
    Returns:
        manual_additions_latest.json 파일 경로
    """
    current_file = Path(__file__).resolve()
    project_root = current_file.parents[3]
    output_dir = project_root / "scout_selector" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    return output_dir / "manual_additions_latest.json"


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
    수동 추가 종목 파일 저장 (날짜별 + latest)
    
    Args:
        data: 저장할 데이터 딕셔너리
        date: 날짜 (YYYYMMDD, None이면 오늘)
        
    Returns:
        성공 여부
    """
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    
    # updated_at 갱신
    data["updated_at"] = datetime.now().isoformat()
    data["date"] = date  # 날짜 보장
    
    # 1. 날짜별 파일 저장
    file_path = get_manual_additions_file(date)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[ERROR] manual_additions 날짜별 파일 저장 실패: {file_path} - {e}")
        return False
    
    # 2. latest 파일도 갱신
    latest_file = get_manual_additions_latest_file()
    try:
        with open(latest_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] manual_additions_latest.json 갱신 실패: {latest_file} - {e}")
        # latest 실패해도 날짜별 저장은 성공했으므로 True 반환
    
    return True


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
    수동 추가 종목 코드 리스트 반환 (당일 한정)
    
    텔레그램 /add로 추가된 종목은 사용자의 즉시 개입을 위한 당일 한정 감시 대상이며,
    장 마감 후 자동으로 제거됩니다.
    
    Args:
        date: 날짜 (YYYYMMDD, None이면 오늘)
        
    Returns:
        종목 코드 리스트 (당일 파일만 읽음)
    """
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    
    # 오늘 날짜의 파일만 로드
    data = load_manual_additions(date)
    
    symbols = []
    for item in data.get("symbols", []):
        symbol = item.get("symbol") if isinstance(item, dict) else item
        if symbol:
            symbols.append(str(symbol).zfill(6))  # 6자리로 정규화
    
    return sorted(list(set(symbols)))  # 중복 제거


def archive_manual_additions_to_history(date: Optional[str] = None) -> Dict:
    """
    수동 추가 종목을 history로 아카이브 (장 마감/파이프라인 종료 시)
    - history/YYYY/MM/YYYYMMDD/manual_additions.json으로 복사
    - manual_additions_latest.json도 함께 복사
    
    Args:
        date: 날짜 (YYYYMMDD, None이면 오늘)
        
    Returns:
        아카이브 결과 딕셔너리 ({"archived": True/False, "date": "...", "symbols": [...]})
    """
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    
    result = {
        "date": date,
        "archived": False,
        "symbols": [],
    }
    
    # latest 파일 확인
    latest_file = get_manual_additions_latest_file()
    
    if not latest_file.exists():
        # latest 파일이 없으면 날짜별 파일 확인
        date_file = get_manual_additions_file(date)
        if not date_file.exists():
            print(f"[INFO] 수동 추가 종목 파일 없음 (아카이브할 파일 없음): {date}")
            return result
        
        # 날짜별 파일을 latest로 복사 후 사용
        try:
            import shutil
            shutil.copy2(str(date_file), str(latest_file))
        except Exception as e:
            print(f"[WARN] 날짜별 파일을 latest로 복사 실패: {e}")
    
    # latest 파일 로드
    try:
        with open(latest_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        result["symbols"] = data.get("symbols", [])
    except Exception as e:
        print(f"[WARN] latest 파일 로드 실패: {e}")
        return result
    
    # history 디렉터리 생성 및 복사
    try:
        current_file = Path(__file__).resolve()
        project_root = current_file.parents[3]
        history_dir = project_root / "scout_selector" / "history" / date[:4] / date[4:6] / date
        history_dir.mkdir(parents=True, exist_ok=True)
        
        # history로 복사
        history_file = history_dir / "manual_additions.json"
        import shutil
        shutil.copy2(str(latest_file), str(history_file))
        
        result["archived"] = True
        print(f"[INFO] 수동 추가 종목 아카이브 완료: {latest_file.name} → history/{date[:4]}/{date[4:6]}/{date}/manual_additions.json")
    except Exception as e:
        print(f"[ERROR] 수동 추가 종목 아카이브 실패: {e}")
        result["error"] = str(e)
    
    return result


def clear_manual_additions(date: Optional[str] = None) -> Dict:
    """
    수동 추가 종목 파일 삭제 (장 마감 후 자동 제거용)
    - 아카이브 후 파일 삭제
    - latest 파일도 초기화 (빈 구조로)
    
    Args:
        date: 날짜 (YYYYMMDD, None이면 오늘)
        
    Returns:
        삭제된 종목 정보 딕셔너리 ({"symbols": [...], "date": "...", "deleted": True/False})
    """
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    
    # 1. 먼저 history로 아카이브
    archive_result = archive_manual_additions_to_history(date)
    
    # 2. 날짜별 파일 삭제
    file_path = get_manual_additions_file(date)
    deleted_data = {
        "date": date,
        "symbols": archive_result.get("symbols", []),
        "deleted": False,
        "archived": archive_result.get("archived", False),
    }
    
    if file_path.exists():
        try:
            file_path.unlink()
            deleted_data["deleted"] = True
            print(f"[INFO] 수동 추가 종목 파일 삭제됨: {file_path.name} (종목 {len(deleted_data['symbols'])}개)")
        except Exception as e:
            print(f"[ERROR] 수동 추가 종목 파일 삭제 실패: {file_path} - {e}")
            deleted_data["error"] = str(e)
    
    # 3. latest 파일 초기화 (빈 구조로)
    latest_file = get_manual_additions_latest_file()
    try:
        empty_data = {
            "date": date,
            "updated_at": datetime.now().isoformat(),
            "source": "telegram",
            "symbols": [],
        }
        with open(latest_file, "w", encoding="utf-8") as f:
            json.dump(empty_data, f, ensure_ascii=False, indent=2)
        print(f"[INFO] manual_additions_latest.json 초기화 완료")
    except Exception as e:
        print(f"[WARN] manual_additions_latest.json 초기화 실패: {e}")
    
    return deleted_data

