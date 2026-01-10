# ===============================
# 캔들기록봇 (OHLCV Collector) v1
# ===============================
"""
캔들기록봇 실행 스크립트

역할:
- 장 마감 후 배치 프로세스로 실행
- 대기실장봇 출력(candidate_pool_YYYYMMDD.json)을 입력으로 받아 일봉 OHLCV 수집
- 문지기봇이 사용할 ohlcv_YYYYMMDD.csv 생성

실행 시점:
- 장 마감 후 (15:35 이후)
- 외부 오케스트레이션(Windows Task Scheduler 등)에 의해 트리거

핵심 원칙:
- 사실 기록만 수행 (Source of Truth)
- 부분 실패 허용, 전체 중단 금지
- 재현 가능성 (같은 입력 → 같은 출력)
"""
from __future__ import annotations

import argparse
import csv
import sys
import io
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set, Optional

# Windows 콘솔 인코딩 설정
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# =========================
# Constants
# =========================

COLLECTOR_NAME = "캔들기록봇"
COLLECTOR_VERSION = "1.0.0"

# 고정 기준 종목 (Cold Start용)
FIXED_SYMBOLS = ["005930", "000660"]  # 삼성전자, SK하이닉스

# CSV 컬럼 순서
CSV_COLUMNS = ["date", "symbol", "open", "high", "low", "close", "volume", "turnover_krw"]

# =========================
# Paths
# =========================

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "data"
INPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(exist_ok=True)


# =========================
# OHLCV Data Collection
# =========================

def collect_ohlcv_pykrx(symbol: str, date: str) -> Optional[Dict]:
    """
    pykrx를 사용하여 일봉 OHLCV 수집
    
    Args:
        symbol: 종목 코드
        date: 날짜 (YYYYMMDD)
        
    Returns:
        OHLCV 데이터 딕셔너리 또는 None (실패 시)
    """
    try:
        from pykrx import stock
        
        # 날짜 형식 변환 (YYYYMMDD -> YYYY-MM-DD)
        date_str = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
        
        # 일봉 데이터 수집
        df = stock.get_market_ohlcv_by_date(date_str, date_str, symbol)
        
        if df is None or df.empty:
            return None
        
        # 첫 번째 행(해당 날짜) 추출
        row = df.iloc[0]
        
        # 거래대금 계산 (종가 * 거래량)
        close = int(row['종가'])
        volume = int(row['거래량'])
        turnover_krw = close * volume
        
        return {
            "date": date,
            "symbol": symbol,
            "open": int(row['시가']),
            "high": int(row['고가']),
            "low": int(row['저가']),
            "close": close,
            "volume": volume,
            "turnover_krw": turnover_krw,
        }
        
    except ImportError:
        print(f"  ⚠️  pykrx 모듈이 없습니다.")
        print(f"      설치 방법: pip install pykrx")
        print(f"      또는: pip install -r requirements-run.txt")
        return None
    except Exception as e:
        print(f"  ⚠️  {symbol} 수집 실패: {e}")
        return None


def collect_ohlcv_batch(symbols: List[str], date: str) -> List[Dict]:
    """
    여러 종목의 OHLCV 일괄 수집
    
    Args:
        symbols: 종목 코드 리스트
        date: 날짜 (YYYYMMDD)
        
    Returns:
        수집 성공한 OHLCV 데이터 리스트
    """
    results = []
    total = len(symbols)
    
    print(f"\n📊 OHLCV 수집 시작 ({total}종목)")
    
    for idx, symbol in enumerate(symbols, 1):
        print(f"  [{idx}/{total}] {symbol}...", end=" ", flush=True)
        
        data = collect_ohlcv_pykrx(symbol, date)
        
        if data:
            results.append(data)
            print("✅")
        else:
            print("❌")
    
    print(f"\n✅ 수집 완료: {len(results)}/{total} 성공")
    
    return results


# =========================
# Input Loading
# =========================

def load_candidate_pool(date: str) -> Set[str]:
    """
    대기실장봇 출력에서 종목 리스트 로드
    
    우선순위:
    1. latest.json (오늘 날짜인 경우 운영 편의용)
    2. history/YYYY/MM/candidate_pool_YYYYMMDD.json (날짜별 파일)
    3. output/candidate_pool_YYYYMMDD.json (구버전 호환)
    
    Args:
        date: 날짜 (YYYYMMDD)
        
    Returns:
        종목 코드 set
    """
    symbols = set()
    
    try:
        import json
        
        # 1. latest.json 우선 시도 (오늘 날짜인 경우)
        today_str = datetime.now().strftime("%Y%m%d")
        if date == today_str:
            latest_file = INPUT_DIR / "latest.json"
            if latest_file.exists():
                try:
                    with open(latest_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    symbols.update(data.get("symbols", []))
                    print(f"  ✅ 대기실장봇 출력 로드 (latest.json): {len(symbols)}종목")
                    return symbols
                except Exception as e:
                    print(f"  ⚠️  latest.json 로드 실패: {e}")
        
        # 2. history/YYYY/MM/candidate_pool_YYYYMMDD.json 시도
        year = date[:4]
        month = date[4:6]
        history_file = INPUT_DIR / "history" / year / month / f"candidate_pool_{date}.json"
        if history_file.exists():
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                symbols.update(data.get("symbols", []))
                print(f"  ✅ 대기실장봇 출력 로드 (history): {len(symbols)}종목")
                return symbols
            except Exception as e:
                print(f"  ⚠️  history 파일 로드 실패: {e}")
        
        # 3. 구버전 호환: output/candidate_pool_YYYYMMDD.json
        candidate_file = INPUT_DIR / f"candidate_pool_{date}.json"
        if candidate_file.exists():
            with open(candidate_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            symbols.update(data.get("symbols", []))
            print(f"  ✅ 대기실장봇 출력 로드 (구버전): {len(symbols)}종목")
        else:
            print(f"  ℹ️  대기실장봇 출력 없음: candidate_pool_{date}.json")
            
    except Exception as e:
        print(f"  ⚠️  대기실장봇 출력 로드 실패: {e}")
    
    return symbols


def load_symbols_file(file_path: Path) -> Set[str]:
    """
    수동 종목 리스트 파일 로드 (Cold Start 보조 입력)
    
    Args:
        file_path: 파일 경로
        
    Returns:
        종목 코드 set
    """
    symbols = set()
    
    try:
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    symbol = line.strip()
                    if symbol and symbol.isdigit():
                        symbols.add(symbol)
            
            print(f"  ✅ 수동 리스트 로드: {len(symbols)}종목")
        else:
            print(f"  ⚠️  파일 없음: {file_path}")
            
    except Exception as e:
        print(f"  ⚠️  수동 리스트 로드 실패: {e}")
    
    return symbols


def collect_input_symbols(date: str, symbols_file: Optional[Path] = None) -> List[str]:
    """
    모든 입력 소스에서 종목 리스트 수집 및 병합
    
    Args:
        date: 날짜 (YYYYMMDD)
        symbols_file: 수동 종목 리스트 파일 경로 (옵션)
        
    Returns:
        병합된 종목 코드 리스트 (정렬됨)
    """
    all_symbols = set()
    
    print(f"\n📥 입력 소스 수집 중...")
    
    # 1. 대기실장봇 출력
    print(f"\n1️⃣ 대기실장봇 출력")
    candidate_symbols = load_candidate_pool(date)
    all_symbols.update(candidate_symbols)
    
    # 2. 수동 리스트 (옵션)
    if symbols_file:
        print(f"\n2️⃣ 수동 종목 리스트")
        manual_symbols = load_symbols_file(symbols_file)
        all_symbols.update(manual_symbols)
    
    # 3. 고정 기준 종목 (항상 포함)
    print(f"\n3️⃣ 고정 기준 종목")
    all_symbols.update(FIXED_SYMBOLS)
    print(f"   포함: {len(FIXED_SYMBOLS)}개 ({', '.join(sorted(FIXED_SYMBOLS))})")
    
    # 중복 제거 및 정렬
    result = sorted(list(all_symbols))
    
    print(f"\n✅ 총 입력 종목: {len(result)}개")
    
    return result


# =========================
# CSV Output
# =========================

def save_ohlcv_csv(data: List[Dict], output_file: Path, date: str):
    """
    OHLCV 데이터를 CSV로 저장
    
    Args:
        data: OHLCV 데이터 리스트
        output_file: 출력 파일 경로
        date: 날짜 (YYYYMMDD)
    """
    if not data:
        # 빈 데이터라도 CSV 생성 (최소 행)
        print(f"\n⚠️  수집된 데이터가 없습니다. 빈 CSV 생성...")
        with open(output_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()
        return
    
    # 날짜 필드 정규화 (YYYYMMDD -> YYYY-MM-DD)
    for row in data:
        if "date" in row and len(row["date"]) == 8:
            row["date"] = f"{row['date'][:4]}-{row['date'][4:6]}-{row['date'][6:8]}"
    
    # CSV 저장
    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"\n📁 저장 완료: {output_file}")
    print(f"   총 {len(data)}개 종목 데이터")


# =========================
# Main
# =========================

def main():
    parser = argparse.ArgumentParser(description=f"{COLLECTOR_NAME} - OHLCV 수집")
    parser.add_argument(
        "--date",
        type=str,
        help="날짜 (YYYYMMDD, 기본값: 오늘)",
        default=None,
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="기존 파일이 있어도 재생성",
    )
    parser.add_argument(
        "--symbols-file",
        type=str,
        help="수동 종목 리스트 파일 경로 (옵션)",
        default=None,
    )
    
    args = parser.parse_args()
    
    # 날짜 결정
    if args.date:
        date = args.date
    else:
        date = datetime.now().strftime("%Y%m%d")
    
    # 휴장일 체크
    from scout_selector.utils.market_calendar import is_market_open
    
    if not is_market_open(date):
        print("=" * 60)
        print(f"[INFO] Market closed on {date}")
        print(f"[SKIP] {COLLECTOR_NAME} - market closed")
        print("=" * 60)
        sys.exit(0)  # 정상 종료 (오류 아님)
    
    print("=" * 60)
    print(f"📊 {COLLECTOR_NAME} - OHLCV 수집")
    print("=" * 60)
    print(f"\n📅 날짜: {date}")
    
    # 출력 파일 경로
    output_file = OUTPUT_DIR / f"ohlcv_{date}.csv"
    
    # 멱등성 체크 (기존 파일이 있으면 재생성하지 않음)
    if output_file.exists() and not args.force:
        print(f"\nℹ️  출력 파일이 이미 존재합니다: {output_file.name}")
        print(f"   재생성하려면 --force 옵션을 사용하세요.")
        print("=" * 60)
        return
    
    # 입력 종목 수집
    symbols_file = Path(args.symbols_file) if args.symbols_file else None
    input_symbols = collect_input_symbols(date, symbols_file)
    
    # Cold Start 처리: 입력 종목이 전혀 없는 경우
    if not input_symbols:
        print(f"\n⚠️  입력 종목이 없습니다. 고정 기준 종목만 수집합니다.")
        input_symbols = FIXED_SYMBOLS
    
    # OHLCV 수집
    try:
        ohlcv_data = collect_ohlcv_batch(input_symbols, date)
        
        # CSV 저장
        save_ohlcv_csv(ohlcv_data, output_file, date)
        
        print(f"\n✅ {COLLECTOR_NAME} 완료")
        print(f"   문지기봇이 {output_file.name} 파일을 입력으로 사용합니다.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        
        # 최소 CSV 생성 시도
        print(f"\n⚠️  최소 CSV 생성 시도...")
        try:
            # 고정 종목만 수집 시도
            minimal_data = collect_ohlcv_batch(FIXED_SYMBOLS, date)
            save_ohlcv_csv(minimal_data, output_file, date)
            
            print(f"✅ 최소 CSV 저장 완료: {output_file}")
            print(f"   (고정 종목만 포함: {', '.join(FIXED_SYMBOLS)})")
            
        except Exception as e2:
            print(f"❌ 최소 CSV 생성도 실패: {e2}")
            # 빈 CSV라도 생성
            try:
                with open(output_file, "w", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
                    writer.writeheader()
                print(f"✅ 빈 CSV 생성 완료: {output_file}")
            except Exception as e3:
                print(f"❌ 빈 CSV 생성도 실패: {e3}")
                sys.exit(1)


if __name__ == "__main__":
    main()

