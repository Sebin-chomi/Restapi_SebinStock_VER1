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
    - 경로: scout_selector/output/watchlist_latest.json (작업지시서 준수)
    - 반환: 종목 코드 리스트 (largecap + volume + structure + theme)
    """
    import json
    import os
    from datetime import datetime
    from pathlib import Path
    
    # 프로젝트 루트 기준으로 scout_selector/output 경로 찾기
    current_file = Path(__file__).resolve()
    # test/framework/watchlist/store.py → 프로젝트 루트
    project_root = current_file.parents[3]
    output_dir = project_root / "scout_selector" / "output"
    
    # 작업지시서: watchlist_latest.json만 읽기 (날짜 포함 파일 금지)
    json_path = output_dir / "watchlist_latest.json"
    
    if not json_path.exists():
        # 파일이 없으면 빈 리스트 반환 (Cold Start)
        print(f"[WARN] watchlist_latest.json 파일을 찾을 수 없습니다: {output_dir}")
        print(f"   → Cold Start 모드로 진행합니다")
        return []
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        watchlist = []
        
        # 새로운 구조: watchlist 필드에 단일 리스트로 통합
        if "watchlist" in data:
            for item in data["watchlist"]:
                if isinstance(item, dict):
                    # code 필드 사용
                    symbol = item.get("code") or item.get("symbol", "")
                    if symbol:
                        watchlist.append(str(symbol).zfill(6))
                else:
                    # 구버전 호환: 문자열이나 튜플
                    watchlist.append(str(item[0] if isinstance(item, tuple) else item).zfill(6))
        else:
            # 구버전 호환: largecap/volume/structure/theme 분리 구조
            for category in ["largecap", "volume", "structure", "theme"]:
                if category in data:
                    for item in data[category]:
                        if isinstance(item, dict):
                            symbol = item.get("symbol") or item.get("code", "")
                            if symbol:
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
