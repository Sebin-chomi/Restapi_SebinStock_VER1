# ===============================
# scout_selector/theme_signals.py
# ===============================
"""
Theme Score 신호 수집 (최소 버전)

(A) 조건검색식 포함 여부
(B) 뉴스 키워드 히트 수
(C) 테마 군 동시 상승
"""
from typing import Dict, List, Set, Optional
from pathlib import Path
import pandas as pd


# ===============================
# (A) 조건검색식 포함 여부
# ===============================
def get_condition_hit_list() -> Set[str]:
    """
    조건검색식에 포함된 종목 리스트 반환
    
    Returns:
        조건검색식에 포함된 종목 코드 set
    """
    condition_stocks = set()
    
    # 방법 1: condition_store에서 가져오기
    try:
        import sys
        from pathlib import Path
        # 프로젝트 루트를 경로에 추가
        project_root = Path(__file__).parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        from research.condition_store import get_stocks
        condition_stocks.update(get_stocks())
    except Exception:
        pass
    
    # 방법 2: daily_scan의 조건검색 결과에서 가져오기
    try:
        from test.daily_scan.inputs.kiwoom_conditions import load_condition_result
        # 여러 조건검색 태그 확인
        for tag in ["A_volume_burst", "B_volatility_jump", "C_volume_accum"]:
            try:
                stocks = load_condition_result(tag)
                condition_stocks.update(stocks)
            except Exception:
                continue
    except Exception:
        pass
    
    # 방법 3: 파일에서 읽기 (선택적)
    try:
        condition_file = Path(__file__).parent.parent / "data" / "condition_hits.txt"
        if condition_file.exists():
            with open(condition_file, "r", encoding="utf-8") as f:
                for line in f:
                    symbol = line.strip()
                    if symbol:
                        condition_stocks.add(symbol)
    except Exception:
        pass
    
    return condition_stocks


# ===============================
# (B) 뉴스 키워드 히트 수
# ===============================
def get_news_hit_count(symbol: str) -> int:
    """
    종목의 뉴스 키워드 히트 수 반환
    
    Args:
        symbol: 종목 코드
    
    Returns:
        뉴스 히트 수 (0 이상)
    """
    # TODO: 실제 뉴스 API 연동
    # 현재는 파일 기반으로 구현 (선택적)
    try:
        # scout_selector/data/news_hits.json
        news_file = Path(__file__).parent / "data" / "news_hits.json"
        if news_file.exists():
            import json
            with open(news_file, "r", encoding="utf-8") as f:
                news_data = json.load(f)
                return news_data.get(symbol, 0)
    except Exception:
        pass
    
    return 0


# ===============================
# (C) 테마 군 동시 상승
# ===============================
def check_theme_group_rise(
    symbol: str,
    latest: pd.DataFrame,
    theme_groups: Optional[Dict[str, List[str]]] = None,
) -> bool:
    """
    테마 군 동시 상승 확인
    
    같은 테마 종목 3개 이상이 +3% 이상 상승했는지 확인
    
    Args:
        symbol: 종목 코드
        latest: 최신 데이터 DataFrame (symbol 인덱스)
        theme_groups: 테마 그룹 딕셔너리 {theme_name: [symbols]}
    
    Returns:
        테마 군 동시 상승 여부
    """
    if theme_groups is None:
        # 기본 테마 그룹 (예시)
        theme_groups = {}
    
    # symbol이 속한 테마 찾기
    symbol_themes = [
        theme for theme, symbols in theme_groups.items()
        if symbol in symbols
    ]
    
    if not symbol_themes:
        return False
    
    # 각 테마에서 상승 종목 수 확인
    for theme in symbol_themes:
        theme_symbols = theme_groups[theme]
        
        # 최신 데이터에서 상승 종목 확인
        rise_count = 0
        for sym in theme_symbols:
            if sym not in latest.index:
                continue
            
            row = latest.loc[sym]
            # 전일 대비 상승률 계산 (간단 버전)
            # 실제로는 전일 종가와 비교해야 함
            # 여기서는 hlc_volatility나 trend로 대체
            change_pct = row.get("trend", 0)  # 5일 추세로 대체
            if change_pct >= 0.03:  # +3% 이상
                rise_count += 1
        
        # 같은 테마 종목 3개 이상 상승
        if rise_count >= 3:
            return True
    
    return False


# ===============================
# Theme Score 계산 (최소 버전)
# ===============================
def compute_theme_score_minimal(
    symbol: str,
    latest: pd.DataFrame,
    condition_hit_list: Set[str],
    theme_groups: Optional[Dict[str, List[str]]] = None,
) -> float:
    """
    최소 버전 Theme Score 계산
    
    아래 중 하나라도 있으면 충분:
    (A) 조건검색식 포함 여부 → 1.0
    (B) 뉴스 키워드 히트 수 → min(1.0, news_count * 0.3)
    (C) 테마 군 동시 상승 → 0.5
    
    Args:
        symbol: 종목 코드
        latest: 최신 데이터 DataFrame
        condition_hit_list: 조건검색식 포함 종목 리스트
        theme_groups: 테마 그룹 딕셔너리
    
    Returns:
        Theme Score (0.0 ~ 1.0)
    """
    # (A) 조건검색식 포함 여부
    if symbol in condition_hit_list:
        return 1.0
    
    # (B) 뉴스 키워드 히트 수
    news_count = get_news_hit_count(symbol)
    if news_count > 0:
        news_score = min(1.0, news_count * 0.3)
        # 뉴스만으로도 충분하면 반환
        if news_score >= 1.0:
            return 1.0
    
    # (C) 테마 군 동시 상승
    if symbol in latest.index:
        if check_theme_group_rise(symbol, latest, theme_groups):
            # 테마 군 상승이 있으면 최소 0.5
            # 뉴스 점수와 합산
            return max(0.5, news_count * 0.3)
    
    # 뉴스만 있는 경우
    return news_count * 0.3


# ===============================
# Theme Score Map 생성
# ===============================
def build_theme_score_map(
    symbols: List[str],
    latest: pd.DataFrame,
    theme_groups: Optional[Dict[str, List[str]]] = None,
) -> Dict[str, float]:
    """
    Theme Score Map 생성
    
    Args:
        symbols: 종목 코드 리스트
        latest: 최신 데이터 DataFrame (symbol 인덱스)
        theme_groups: 테마 그룹 딕셔너리
    
    Returns:
        {symbol: theme_score} 딕셔너리
    """
    condition_hit_list = get_condition_hit_list()
    
    theme_score_map = {}
    for symbol in symbols:
        if symbol not in latest.index:
            theme_score_map[symbol] = 0.0
            continue
        
        score = compute_theme_score_minimal(
            symbol,
            latest,
            condition_hit_list,
            theme_groups,
        )
        theme_score_map[symbol] = score
    
    return theme_score_map

