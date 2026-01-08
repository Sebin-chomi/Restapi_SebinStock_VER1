# ===============================
# gatekeeper_bot/theme_score_builder.py
# ===============================
"""
문지기봇 테마 점수 빌더

역할:
- 외부 신호(조건식·뉴스)를 theme_score_map으로 변환
- 문지기봇 핵심 엔진이 사용할 수 있는 형태로 가공

입력: gatekeeper_bot/input/conditions/, gatekeeper_bot/input/news/
출력: {symbol: {score: float, sources: List[str]}} 딕셔너리
"""
from pathlib import Path
import json
import shutil
from collections import defaultdict
from typing import Dict, List, Tuple
from datetime import datetime


def archive_old_signals(input_dir: Path, date: str, history_dir: Path):
    """
    오늘 날짜가 아닌 파일들을 히스토리 디렉토리로 이동
    
    Args:
        input_dir: gatekeeper_bot/input/ 디렉토리
        date: 오늘 날짜 (YYYYMMDD)
        history_dir: 히스토리 저장 디렉토리
    """
    history_dir.mkdir(parents=True, exist_ok=True)
    
    # Conditions 아카이브
    cond_dir = input_dir / "conditions"
    if cond_dir.exists():
        cond_history_dir = history_dir / "conditions"
        cond_history_dir.mkdir(parents=True, exist_ok=True)
        
        for cond_file in cond_dir.glob("conditions_*.json"):
            file_date = cond_file.stem.replace("conditions_", "")
            if file_date != date:
                # 과거 파일을 히스토리로 이동
                dest = cond_history_dir / cond_file.name
                try:
                    shutil.move(str(cond_file), str(dest))
                    print(f"📦 아카이브: {cond_file.name} → {dest}")
                except Exception as e:
                    print(f"⚠️  아카이브 실패: {cond_file.name} - {e}")
    
    # News 아카이브
    news_dir = input_dir / "news"
    if news_dir.exists():
        news_history_dir = history_dir / "news"
        news_history_dir.mkdir(parents=True, exist_ok=True)
        
        for news_file in news_dir.glob("news_*.json"):
            file_date = news_file.stem.replace("news_", "")
            if file_date != date:
                # 과거 파일을 히스토리로 이동
                dest = news_history_dir / news_file.name
                try:
                    shutil.move(str(news_file), str(dest))
                    print(f"📦 아카이브: {news_file.name} → {dest}")
                except Exception as e:
                    print(f"⚠️  아카이브 실패: {news_file.name} - {e}")


def build_theme_score_map(
    input_dir: Path,
    date: str = None,
    archive_history: bool = True,
) -> Dict[str, Dict]:
    """
    외부 신호를 theme_score_map으로 변환 (오늘 날짜만 사용)
    
    Args:
        input_dir: gatekeeper_bot/input/ 디렉토리
        date: 날짜 (YYYYMMDD), None이면 오늘
        archive_history: 과거 파일을 히스토리로 이동할지 여부
    
    Returns:
        {symbol: {score: float, sources: List[str]}} 딕셔너리
    """
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    
    # 히스토리 아카이브 (과거 파일 이동)
    if archive_history:
        history_dir = input_dir.parent / "history" / "input"
        archive_old_signals(input_dir, date, history_dir)
    
    score_map = defaultdict(lambda: {"score": 0.0, "sources": []})
    
    # -------------------------
    # (A) Conditions (오늘 날짜만)
    # -------------------------
    cond_dir = input_dir / "conditions"
    cond_file = cond_dir / f"conditions_{date}.json"
    
    if cond_file.exists():
        try:
            with open(cond_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for cond in data.get("conditions", []):
                    condition_name = cond.get("condition_name", "unknown")
                    source = f"condition:{condition_name}"
                    for sym in cond.get("symbols", []):
                        # 조건식 히트 → 1.0
                        score_map[sym]["score"] = max(score_map[sym]["score"], 1.0)
                        if source not in score_map[sym]["sources"]:
                            score_map[sym]["sources"].append(source)
        except Exception as e:
            print(f"⚠️  조건식 파일 읽기 오류: {e}")
    else:
        print(f"📋 조건식 파일 없음: {cond_file.name}")
    
    # -------------------------
    # (B) News (오늘 날짜만)
    # -------------------------
    news_dir = input_dir / "news"
    news_file = news_dir / f"news_{date}.json"
    
    if news_file.exists():
        try:
            with open(news_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 뉴스 카운트 계산 (같은 종목의 뉴스 개수)
                news_count_by_symbol = defaultdict(int)
                news_sources_by_symbol = defaultdict(list)
                
                for item in data.get("items", []):
                    sym = item.get("symbol")
                    if sym:
                        news_count_by_symbol[sym] += 1
                        # 뉴스 출처 정보 수집
                        keywords = item.get("keywords", [])
                        # 뉴스 출처 형식: "news:{키워드1},{키워드2}" 또는 "news:일반"
                        if keywords:
                            source = f"news:{','.join(keywords[:2])}"  # 최대 2개 키워드
                        else:
                            source = "news:일반"
                        if source not in news_sources_by_symbol[sym]:
                            news_sources_by_symbol[sym].append(source)
                
                # 뉴스 점수 계산
                for sym, news_count in news_count_by_symbol.items():
                    # 뉴스 1건 = 0.3, 3건 이상 = 1.0
                    news_score = min(1.0, news_count * 0.3)
                    # 조건식이 있으면 1.0 유지, 없으면 뉴스 점수
                    score_map[sym]["score"] = max(score_map[sym]["score"], news_score)
                    # 출처 추가
                    for source in news_sources_by_symbol[sym]:
                        if source not in score_map[sym]["sources"]:
                            score_map[sym]["sources"].append(source)
        except Exception as e:
            print(f"⚠️  뉴스 파일 읽기 오류: {e}")
    else:
        print(f"📰 뉴스 파일 없음: {news_file.name}")
    
    # 딕셔너리로 변환 (sources 정렬)
    result = {}
    for sym, data in score_map.items():
        result[sym] = {
            "score": data["score"],
            "sources": sorted(data["sources"])  # 정렬된 출처 리스트
        }
    
    return result
