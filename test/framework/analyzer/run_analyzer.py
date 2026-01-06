# ===============================
# test/framework/analyzer/run_analyzer.py
# ===============================
"""
Post-Market Analyzer 실행 스크립트

사용법:
    python -m test.framework.analyzer.run_analyzer [날짜] [--top100]
    
예시:
    python -m test.framework.analyzer.run_analyzer
    python -m test.framework.analyzer.run_analyzer 2026-01-01
    python -m test.framework.analyzer.run_analyzer 2026-01-01 --top100
"""
import sys
import os

# 프로젝트 루트를 경로에 추가
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../..")
)
sys.path.insert(0, PROJECT_ROOT)

from test.framework.analyzer.post_market_analyzer import analyze_daily_market


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Post-Market Analyzer - 일일 시장 분석"
    )
    parser.add_argument(
        "date",
        nargs="?",
        default=None,
        help="분석할 날짜 (YYYY-MM-DD), 생략 시 오늘"
    )
    parser.add_argument(
        "--top100",
        action="store_true",
        help="상위 100 결과 포함"
    )
    parser.add_argument(
        "--with-graphs",
        action="store_true",
        dest="with_graphs",
        help="그래프 생성 (daily_graphs/ 디렉토리에 저장)"
    )
    
    args = parser.parse_args()
    
    result = analyze_daily_market(
        date=args.date,
        include_top_100=args.top100,
        with_graphs=args.with_graphs,
    )
    
    if "error" in result:
        print(f"\n❌ 오류: {result['message']}")
        sys.exit(1)
    
    print("\n✅ 분석 완료!")
    print(f"\n📁 결과 파일:")
    print(f"   JSON: {result['saved_paths']['json_path']}")
    print(f"   TXT:  {result['saved_paths']['txt_path']}")
    if result['saved_paths'].get('report_path'):
        print(f"   Report: {result['saved_paths']['report_path']}")
    if result['saved_paths'].get('graphs_dir'):
        print(f"   Graphs: {result['saved_paths']['graphs_dir']}")


if __name__ == "__main__":
    main()


