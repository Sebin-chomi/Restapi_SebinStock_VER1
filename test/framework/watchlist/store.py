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
    문지기봇에서 생성한 JSON 파일을 읽어서 watchlist 로드
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
    output_dir = project_root / "scout_selector" / "output"
    json_path = output_dir / f"watchlist_{date}.json"
    
    if not json_path.exists():
        # 파일이 없으면 최신 watchlist 파일로 폴백 시도
        # 1순위: latest_watchlist.json
        latest_path = output_dir / "latest_watchlist.json"
        if latest_path.exists():
            json_path = latest_path
        else:
            # 2순위: 가장 최근 날짜의 watchlist 파일 찾기
            watchlist_files = list(output_dir.glob("watchlist_*.json"))
            if watchlist_files:
                # 파일명에서 날짜 추출하여 정렬 (최신순)
                watchlist_files.sort(key=lambda p: p.stem.split("_")[-1], reverse=True)
                json_path = watchlist_files[0]
                print(f"[SCOUT] 오늘 날짜 watchlist 없음, 최신 파일 사용: {json_path.name}")
            else:
                # 파일이 없으면 빈 리스트 반환 (Cold Start)
                print(f"[WARN] watchlist 파일을 찾을 수 없습니다: {output_dir}")
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
                    symbol = item["symbol"]
                    # 숫자로 저장된 경우 문자열로 변환 (예: 5930 → "005930")
                    watchlist.append(str(symbol).zfill(6))
                else:
                    # 구버전 호환: (code, score) 튜플
                    watchlist.append(str(item[0] if isinstance(item, tuple) else item).zfill(6))
        
        # volume, structure, theme: [{"symbol": code, ...}, ...]
        for category in ["volume", "structure", "theme"]:
            if category in data:
                for item in data[category]:
                    if isinstance(item, dict):
                        symbol = item["symbol"]
                        # 숫자로 저장된 경우 문자열로 변환 (예: 5930 → "005930")
                        watchlist.append(str(symbol).zfill(6))
                    else:
                        # 구버전 호환: (code, score) 튜플
                        watchlist.append(str(item[0] if isinstance(item, tuple) else item).zfill(6))
        
        # 중복 제거 (순서 유지)
        return list(dict.fromkeys(watchlist))
    
    except Exception as e:
        print(f"[WARN] watchlist JSON 로드 실패: {json_path} - {e}")
        return []


def get_watchlist():
    """
    정찰봇 watchlist 반환
    - JSON에서 로드한 종목 + 수동 추가 종목 + 동적 추가 종목 병합
    """
    from datetime import datetime
    
    # 오늘 날짜의 JSON에서 watchlist 로드
    json_watchlist = load_watchlist_from_json()
    
    # 수동 추가 종목 로드 (영속 저장된 것)
    try:
        from test.framework.watchlist.manual_additions import get_manual_symbols
        manual_symbols = get_manual_symbols()
    except Exception as e:
        print(f"[WARN] 수동 추가 종목 로드 실패: {e}")
        manual_symbols = []
    
    # 동적 watchlist와 병합 (중복 제거, 순서 유지)
    # 병합 순서: 자동 선정 종목 → 수동 추가 종목 → 동적 추가 종목
    combined = list(dict.fromkeys(json_watchlist + manual_symbols + _DYNAMIC_WATCHLIST))
    
    # 로그 출력
    print(f"[SCOUT] JSON watchlist: {len(json_watchlist)} symbols")
    if manual_symbols:
        print(f"[SCOUT] manual additions loaded: {len(manual_symbols)} symbols")
    if _DYNAMIC_WATCHLIST:
        print(f"[SCOUT] dynamic watchlist: {len(_DYNAMIC_WATCHLIST)} symbols")
    print(f"[SCOUT] merged watchlist size: {len(combined)} symbols")
    
    return combined


def clear_dynamic():
    _DYNAMIC_WATCHLIST.clear()
