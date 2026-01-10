# ===============================
# test/framework/analyzer/view_scout_results.py
# ===============================
"""
정찰 결과 간단 확인 스크립트

사용법:
    python -m test.framework.analyzer.view_scout_results [날짜]
    
예시:
    python -m test.framework.analyzer.view_scout_results
    python -m test.framework.analyzer.view_scout_results 2026-01-05
"""
import sys
import os
import json
from datetime import datetime
from pathlib import Path

# 프로젝트 루트를 경로에 추가
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../..")
)
sys.path.insert(0, PROJECT_ROOT)

SCOUT_RECORDS_DIR = os.path.join(PROJECT_ROOT, "records", "scout")


def get_scout_date_dir(date: str) -> str:
    """
    날짜를 YYYY/MM/YYYYMMDD 구조의 디렉터리 경로로 변환
    
    Args:
        date: 날짜 (YYYY-MM-DD 형식)
        
    Returns:
        YYYY/MM/YYYYMMDD 구조의 디렉터리 경로
    """
    # YYYY-MM-DD → YYYY, MM, YYYYMMDD 추출
    year, month, day = date.split("-")
    date_compact = f"{year}{month}{day}"
    
    # YYYY/MM/YYYYMMDD 구조로 경로 생성
    date_dir = os.path.join(SCOUT_RECORDS_DIR, year, month, date_compact)
    return date_dir


def view_scout_results(date: str = None):
    """정찰 결과 간단 확인"""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    # YYYY/MM/YYYYMMDD 구조로 디렉터리 경로 생성
    date_dir = get_scout_date_dir(date)
    
    if not os.path.exists(date_dir):
        print(f"❌ {date}의 정찰 기록이 없습니다.")
        print(f"   경로: {date_dir}")
        return
    
    print("=" * 60)
    print(f"📊 정찰 결과 확인 - {date}")
    print("=" * 60)
    
    # 모든 JSONL 파일 읽기
    jsonl_files = list(Path(date_dir).glob("*.jsonl"))
    
    if not jsonl_files:
        print(f"⚠️  {date}에 기록된 파일이 없습니다.")
        return
    
    total_records = 0
    stock_stats = {}
    
    for jsonl_file in sorted(jsonl_files):
        stock_code = jsonl_file.stem
        records = 0  # count → records
        triggered_records = 0  # observer_triggered → triggered_records
        
        try:
            with open(jsonl_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        records += 1
                        total_records += 1
                        
                        # trigger: 관측 조건을 만족한 '사건'
                        if record.get("observer", {}).get("triggered", False):
                            triggered_records += 1
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"⚠️  {stock_code}.jsonl 읽기 오류: {e}")
            continue
        
        stock_stats[stock_code] = {
            "records": records,  # count → records
            "triggered_records": triggered_records,  # observer_triggered → triggered_records
        }
    
    # 요약 출력
    print(f"\n📈 총 기록 수 (total_records): {total_records}개")
    print(f"📋 관찰 종목 수: {len(stock_stats)}개\n")
    
    print("종목별 상세:")
    print("-" * 60)
    for stock_code, stats in sorted(stock_stats.items()):
        trigger_rate = (
            stats["triggered_records"] / stats["records"] * 100
            if stats["records"] > 0
            else 0
        )
        print(
            f"  {stock_code}: "
            f"{stats['records']} records, "
            f"Triggered {stats['triggered_records']} records "
            f"({trigger_rate:.1f}%)"
        )
    
    print("\n" + "=" * 60)
    print(f"📁 원본 파일 위치: {date_dir}")
    print(f"💡 상세 분석은 다음 명령어로 실행:")
    print(f"   python -m test.framework.analyzer.run_analyzer {date}")
    print("=" * 60)


if __name__ == "__main__":
    date = None
    if len(sys.argv) > 1:
        date = sys.argv[1]
    
    view_scout_results(date)

