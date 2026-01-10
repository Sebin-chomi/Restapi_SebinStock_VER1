# ===============================
# test/framework/analyzer/auto_analyzer.py
# ===============================
"""
Post-Market Analyzer 자동 실행 스크립트

장 마감 후 자동으로 분석 및 그래프 생성
Windows 작업 스케줄러와 함께 사용
"""
import sys
import os
from datetime import datetime

# 프로젝트 루트를 경로에 추가
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../..")
)
sys.path.insert(0, PROJECT_ROOT)

from test.framework.analyzer.post_market_analyzer import analyze_daily_market


def main():
    """자동 분석 실행 (그래프 포함)"""
    print("=" * 60)
    print("Post-Market Analyzer 자동 실행")
    print("그래프 포함 분석")
    print("=" * 60)
    print()
    
    # 오늘 날짜로 분석 실행 (그래프 포함)
    result = analyze_daily_market(
        date=None,  # 오늘 날짜
        include_top_100=False,
        with_graphs=True,  # 그래프 자동 생성
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
    
    return 0


if __name__ == "__main__":
    sys.exit(main())











