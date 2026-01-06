# 정찰봇 감시 종목 (동적 주입용)
_DYNAMIC_WATCHLIST = []


MAX_DYNAMIC = 6


def add_stock(stk_cd: str):
    if stk_cd in _DYNAMIC_WATCHLIST:
        return
    if len(_DYNAMIC_WATCHLIST) >= MAX_DYNAMIC:
        return
    _DYNAMIC_WATCHLIST.append(stk_cd)


def remove_stock(stk_cd: str):
    if stk_cd in _DYNAMIC_WATCHLIST:
        _DYNAMIC_WATCHLIST.remove(stk_cd)


def load_watchlist_from_json(date: str | None = None) -> list[str]:
    """
    scout_selector에서 생성한 JSON 파일을 읽어서 watchlist 로드
    - 경로: scout_selector/output/watchlist_YYYYMMDD.json
    - 반환: 종목 코드 리스트 (largecap + volume + structure + theme)
    """
    import json
    import os
    from datetime import datetime
    from pathlib import Path
    
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    
    # 프로젝트 루트 기준으로 scout_selector/output 경로 찾기
    current_file = Path(__file__).resolve()
    # test/framework/watchlist/store.py → 프로젝트 루트
    project_root = current_file.parents[3]
    json_path = project_root / "scout_selector" / "output" / f"watchlist_{date}.json"
    
    if not json_path.exists():
        # 파일이 없으면 빈 리스트 반환 (Cold Start)
        return []
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 모든 카테고리의 종목 코드 추출
        watchlist = []
        
        # largecap: [{"symbol": code, ...}, ...]
        if "largecap" in data:
            for item in data["largecap"]:
                if isinstance(item, dict):
                    watchlist.append(item["symbol"])
                else:
                    # 구버전 호환: (code, score) 튜플
                    watchlist.append(item[0] if isinstance(item, tuple) else item)
        
        # volume, structure, theme: [{"symbol": code, ...}, ...]
        for category in ["volume", "structure", "theme"]:
            if category in data:
                for item in data[category]:
                    if isinstance(item, dict):
                        watchlist.append(item["symbol"])
                    else:
                        # 구버전 호환: (code, score) 튜플
                        watchlist.append(item[0] if isinstance(item, tuple) else item)
        
        # 중복 제거 (순서 유지)
        return list(dict.fromkeys(watchlist))
    
    except Exception as e:
        print(f"[WARN] watchlist JSON 로드 실패: {json_path} - {e}")
        return []


def get_watchlist():
    """
    정찰봇 watchlist 반환
    - JSON에서 로드한 종목 + 동적 추가 종목 병합
    """
    from datetime import datetime
    
    # 오늘 날짜의 JSON에서 watchlist 로드
    json_watchlist = load_watchlist_from_json()
    
    # 동적 watchlist와 병합 (중복 제거, 순서 유지)
    combined = list(dict.fromkeys(json_watchlist + _DYNAMIC_WATCHLIST))
    
    return combined


def clear_dynamic():
    _DYNAMIC_WATCHLIST.clear()
