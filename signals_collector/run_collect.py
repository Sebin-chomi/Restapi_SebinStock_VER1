# ===============================
# signals_collector/run_collect.py
# ===============================
"""
신호 수집 실행 스크립트

장 마감 후 1회 실행 (또는 스케줄)
- 조건식 수집 → scout_selector/input/conditions/conditions_YYYYMMDD.json
- 뉴스 수집 → scout_selector/input/news/news_YYYYMMDD.json
"""
import sys
from pathlib import Path
from datetime import datetime
import argparse

# 프로젝트 루트를 경로에 추가
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from signals_collector.collectors.condition_kiwoom import collect_conditions
from signals_collector.collectors.news_provider import collect_news
from signals_collector.utils.telegram_notifier import notify_collection_failure


# ===============================
# 경로 설정
# ===============================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_ROOT / "scout_selector" / "input"
CONDITIONS_DIR = INPUT_DIR / "conditions"
NEWS_DIR = INPUT_DIR / "news"


# ===============================
# 메인 함수
# ===============================

def main(date: str = None, condition_names: list = None):
    """
    신호 수집 실행
    
    Args:
        date: 날짜 (YYYYMMDD), None이면 오늘
        condition_names: 수집할 조건식 이름 리스트 (None이면 모든 조건식)
    """
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    
    print("="*60)
    print("📡 신호 수집 시작")
    print("="*60)
    print(f"📅 날짜: {date}")
    print(f"📁 출력 디렉토리: {INPUT_DIR}")
    print()
    
    # =========================
    # 1. 조건식 수집
    # =========================
    print("="*60)
    print("📋 조건식 수집")
    print("="*60)
    
    try:
        success = collect_conditions(
            output_dir=CONDITIONS_DIR,
            date=date,
            condition_names=condition_names,
        )
        if success:
            print("✅ 조건식 수집 성공")
        else:
            print("⚠️  조건식 수집 실패 (빈 파일 생성됨)")
            notify_collection_failure("조건식", "수집 실패 (빈 파일 생성)", date)
    except Exception as e:
        print(f"❌ 조건식 수집 오류: {e}")
        # 파이프라인 안전장치: 빈 파일 생성
        CONDITIONS_DIR.mkdir(parents=True, exist_ok=True)
        output_file = CONDITIONS_DIR / f"conditions_{date}.json"
        import json
        empty_data = {
            "date": date,
            "source": "kiwoom_condition",
            "conditions": []
        }
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(empty_data, f, ensure_ascii=False, indent=2)
        print(f"📋 빈 조건식 파일 생성: {output_file}")
        notify_collection_failure("조건식", str(e), date)
    
    print()
    
    # =========================
    # 2. 뉴스 수집
    # =========================
    print("="*60)
    print("📰 뉴스 수집")
    print("="*60)
    
    try:
        success = collect_news(
            output_dir=NEWS_DIR,
            date=date,
            use_api=False,  # 실제 API 연동 시 True로 변경
            api_config=None,
        )
        if success:
            print("✅ 뉴스 수집 성공")
        else:
            print("⚠️  뉴스 수집 실패 (빈 파일 생성됨)")
            notify_collection_failure("뉴스", "수집 실패 (빈 파일 생성)", date)
    except Exception as e:
        print(f"❌ 뉴스 수집 오류: {e}")
        # 파이프라인 안전장치: 빈 파일 생성
        NEWS_DIR.mkdir(parents=True, exist_ok=True)
        output_file = NEWS_DIR / f"news_{date}.json"
        import json
        empty_data = {
            "date": date,
            "source": "naver_news",
            "items": []
        }
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(empty_data, f, ensure_ascii=False, indent=2)
        print(f"📰 빈 뉴스 파일 생성: {output_file}")
        notify_collection_failure("뉴스", str(e), date)
    
    print()
    
    # =========================
    # 완료
    # =========================
    print("="*60)
    print("✅ 신호 수집 완료")
    print("="*60)
    print(f"📁 생성된 파일:")
    print(f"   - {CONDITIONS_DIR / f'conditions_{date}.json'}")
    print(f"   - {NEWS_DIR / f'news_{date}.json'}")
    print()
    print("💡 다음 단계:")
    print("   scout_selector/runner.py 실행 → theme_score_map 생성")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="신호 수집 실행")
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="날짜 (YYYYMMDD), 기본값: 오늘"
    )
    parser.add_argument(
        "--conditions",
        type=str,
        nargs="+",
        default=None,
        help="수집할 조건식 이름 리스트 (기본값: 모든 조건식)"
    )
    
    args = parser.parse_args()
    
    main(
        date=args.date,
        condition_names=args.conditions,
    )

