# ===============================
# signals_collector/collectors/news_provider.py
# ===============================
"""
뉴스 수집기

당일 뉴스에서 종목별 히트(건수/키워드)를 추출하여
gatekeeper_bot/input/news/news_YYYYMMDD.json 생성
"""
import sys
from pathlib import Path
from typing import List, Dict, Optional
import json
import re
from datetime import datetime
from collections import defaultdict

# 프로젝트 루트를 경로에 추가
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_BEAUTIFULSOUP = True
except ImportError:
    HAS_BEAUTIFULSOUP = False
    print("⚠️  BeautifulSoup4가 설치되지 않았습니다. pip install beautifulsoup4")


# ===============================
# 키워드 추출
# ===============================

# 주식 관련 키워드 (자동 추출용)
STOCK_KEYWORDS = [
    "AI", "인공지능", "반도체", "바이오", "제약", "전기차", "배터리",
    "2차전지", "수소", "신재생", "태양광", "풍력", "로봇", "드론",
    "클라우드", "메타버스", "블록체인", "암호화폐", "NFT", "게임",
    "엔터", "콘텐츠", "OTT", "이커머스", "배달", "물류", "건설",
    "부동산", "은행", "증권", "보험", "화학", "철강", "조선",
    "자동차", "항공", "해운", "석유", "가스", "전력", "통신",
    "5G", "6G", "스마트폰", "디스플레이", "패널", "반도체장비",
    "소재", "부품", "기계", "전기전자", "IT", "소프트웨어",
    "플랫폼", "핀테크", "핀테크", "핀테크", "핀테크",
]

def extract_keywords(text: str, max_keywords: int = 3) -> List[str]:
    """
    텍스트에서 키워드 추출
    
    Args:
        text: 추출할 텍스트
        max_keywords: 최대 키워드 개수
    
    Returns:
        키워드 리스트
    """
    if not text:
        return []
    
    # 대소문자 구분 없이 매칭
    text_lower = text.lower()
    found_keywords = []
    
    for keyword in STOCK_KEYWORDS:
        if keyword.lower() in text_lower:
            if keyword not in found_keywords:
                found_keywords.append(keyword)
                if len(found_keywords) >= max_keywords:
                    break
    
    return found_keywords


# ===============================
# 네이버 뉴스 수집
# ===============================

def collect_naver_news_rss(query: str, max_items: int = 10) -> List[Dict]:
    """
    네이버 뉴스 RSS에서 수집
    
    Args:
        query: 검색어 (종목명 등)
        max_items: 최대 수집 개수
    
    Returns:
        뉴스 아이템 리스트
    """
    if not HAS_BEAUTIFULSOUP:
        return []
    
    try:
        # 네이버 뉴스 RSS URL
        url = f"https://search.naver.com/search.naver?where=news&query={query}&sm=jtb&ie=utf8"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        news_items = []
        
        # 뉴스 제목과 링크 추출
        news_articles = soup.select("div.news_area")[:max_items]
        
        for article in news_articles:
            title_elem = article.select_one("a.news_tit")
            if not title_elem:
                continue
            
            title = title_elem.get_text(strip=True)
            link = title_elem.get("href", "")
            
            # 키워드 추출
            keywords = extract_keywords(title)
            
            news_items.append({
                "headline": title,
                "link": link,
                "keywords": keywords,
            })
        
        return news_items
    
    except Exception as e:
        print(f"⚠️  네이버 뉴스 수집 오류: {e}")
        return []


# ===============================
# 종목명 매칭
# ===============================

def get_stock_symbols_from_watchlist() -> List[str]:
    """
    watchlist에서 종목 코드 리스트 가져오기
    
    Returns:
        종목 코드 리스트
    """
    try:
        # 최근 watchlist 파일 찾기
        watchlist_dir = PROJECT_ROOT / "gatekeeper_bot" / "output"
        watchlist_files = sorted(watchlist_dir.glob("watchlist_*.json"), reverse=True)
        
        if not watchlist_files:
            return []
        
        with open(watchlist_files[0], "r", encoding="utf-8") as f:
            data = json.load(f)
        
        symbols = []
        for category in ["largecap", "volume", "structure", "theme"]:
            for item in data.get(category, []):
                symbol = item.get("symbol")
                if symbol:
                    symbols.append(symbol)
        
        return list(set(symbols))  # 중복 제거
    
    except Exception as e:
        print(f"⚠️  watchlist 읽기 오류: {e}")
        return []


def get_stock_name(symbol: str) -> Optional[str]:
    """
    종목 코드로 종목명 가져오기
    
    Args:
        symbol: 종목 코드
    
    Returns:
        종목명 (없으면 None)
    """
    try:
        # 간단한 매핑 (실제로는 API 호출 필요)
        # TODO: 실제 종목명 API 연동
        return None
    except Exception:
        return None


# ===============================
# 뉴스 수집 (최소 버전)
# ===============================

def collect_news_from_mock(
    output_dir: Path,
    date: str,
) -> bool:
    """
    MOCK 뉴스 수집 (실제 API 연동 전까지 사용)
    
    Args:
        output_dir: gatekeeper_bot/input/news/ 디렉토리
        date: 날짜 (YYYYMMDD)
    
    Returns:
        성공 여부
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"news_{date}.json"
    
    # 빈 JSON 생성 (파이프라인 안전장치)
    empty_data = {
        "date": date,
        "source": "naver_news",
        "items": []
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(empty_data, f, ensure_ascii=False, indent=2)
    
    print(f"📰 뉴스 수집 완료 (MOCK): {output_file}")
    print(f"   실제 뉴스 API 연동 필요")
    
    return True


def collect_news_from_api(
    output_dir: Path,
    date: str,
    api_config: Optional[Dict] = None,
) -> bool:
    """
    실제 뉴스 API에서 수집
    
    Args:
        output_dir: gatekeeper_bot/input/news/ 디렉토리
        date: 날짜 (YYYYMMDD)
        api_config: API 설정 딕셔너리
    
    Returns:
        성공 여부
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"news_{date}.json"
    
    # 종목 리스트 가져오기
    symbols = get_stock_symbols_from_watchlist()
    
    if not symbols:
        print("⚠️  종목 리스트가 비어있습니다. watchlist 파일을 확인하세요.")
        # 빈 JSON 생성
        empty_data = {
            "date": date,
            "source": "naver_news",
            "items": []
        }
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(empty_data, f, ensure_ascii=False, indent=2)
        return False
    
    print(f"📰 {len(symbols)}개 종목 뉴스 수집 중...")
    
    all_items = []
    
    # 각 종목별 뉴스 수집
    for symbol in symbols[:20]:  # 최대 20개 종목만 (API 제한 고려)
        try:
            # 종목명 가져오기 (실제로는 API 호출)
            stock_name = get_stock_name(symbol)
            query = stock_name if stock_name else symbol
            
            # 네이버 뉴스 수집
            news_items = collect_naver_news_rss(query, max_items=5)
            
            for item in news_items:
                all_items.append({
                    "symbol": symbol,
                    "headline": item.get("headline", ""),
                    "keywords": item.get("keywords", []),
                    "published_at": datetime.now().isoformat(),  # 실제 발행 시각은 API에서 가져와야 함
                })
        
        except Exception as e:
            print(f"⚠️  종목 {symbol} 뉴스 수집 오류: {e}")
            continue
    
    # JSON 저장
    output_data = {
        "date": date,
        "source": "naver_news",
        "items": all_items
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 뉴스 수집 완료: {output_file}")
    print(f"   총 {len(all_items)}건 뉴스 수집")
    
    return True


def collect_news(
    output_dir: Path,
    date: str,
    use_api: bool = False,
    api_config: Optional[Dict] = None,
) -> bool:
    """
    뉴스 수집 (통합 함수)
    
    Args:
        output_dir: gatekeeper_bot/input/news/ 디렉토리
        date: 날짜 (YYYYMMDD)
        use_api: 실제 API 사용 여부
        api_config: API 설정 딕셔너리
    
    Returns:
        성공 여부
    """
    if use_api and api_config:
        return collect_news_from_api(output_dir, date, api_config)
    else:
        return collect_news_from_mock(output_dir, date)
