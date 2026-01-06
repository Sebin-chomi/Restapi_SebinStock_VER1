# ===============================
# scout_selector/prepare_tomorrow.py
# 내일 사용할 종목을 지금 선정하는 스크립트
# ===============================
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict

import pandas as pd

from selector import (
    SelectorConfig,
    select_watchlist,
    compute_features,
)

# =========================
# Paths
# =========================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# =========================
# Helper Functions
# =========================

def infer_phase(df: pd.DataFrame, lookback: int = 20) -> str:
    """Phase 자동 추론"""
    if df.empty or "symbol" not in df.columns or "date" not in df.columns:
        return "warmup"
    
    try:
        max_days = (
            df.groupby("symbol")["date"]
            .nunique()
            .max()
        )
        if pd.isna(max_days) or max_days == 0:
            return "warmup"
        return "normal" if max_days >= lookback else "warmup"
    except Exception:
        return "warmup"


# =========================
# Main
# =========================

def main():
    print("="*60)
    print("📋 내일 사용할 종목 선정")
    print("="*60)
    
    # 내일 날짜
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_str = tomorrow.strftime("%Y%m%d")
    
    print(f"\n📅 내일 날짜: {tomorrow_str}")
    
    # 데이터 파일 찾기 (어제 또는 오늘 데이터 사용)
    data_files = []
    for days_ago in range(5):  # 최근 5일 데이터 확인
        check_date = datetime.now() - timedelta(days=days_ago)
        check_file = DATA_DIR / f"ohlcv_{check_date.strftime('%Y%m%d')}.csv"
        if check_file.exists():
            data_files.append((check_file, check_date))
    
    if not data_files:
        print(f"\n⚠️  데이터 파일을 찾을 수 없습니다.")
        print(f"   {DATA_DIR}/ohlcv_YYYYMMDD.csv 형식의 파일이 필요합니다.")
        print(f"\n💡 옵션:")
        print(f"   1. 어제 데이터 파일을 준비하세요")
        print(f"   2. 또는 수동으로 종목을 입력하세요 (아래 참고)")
        return
    
    # 가장 최근 데이터 사용
    data_file, data_date = data_files[0]
    print(f"📊 사용할 데이터: {data_file.name} ({data_date.strftime('%Y-%m-%d')})")
    
    # 데이터 로드
    df = pd.read_csv(data_file)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    
    print(f"   종목 수: {df['symbol'].nunique()} 종목")
    print(f"   데이터 기간: {df['date'].min()} ~ {df['date'].max()}")
    
    # Phase 추론
    phase = infer_phase(df)
    print(f"   Phase: {phase}")
    
    # Config
    CFG = SelectorConfig(phase=phase)
    LARGECAPS = ["005930", "000660"]
    
    # Feature 계산
    df_feat = compute_features(df, CFG)
    
    # Theme Score Map 빌드 (표준 입력 경로, 내일 날짜만 사용)
    from theme_score_builder import build_theme_score_map
    
    INPUT_DIR = BASE_DIR / "input"
    tomorrow_date = tomorrow.strftime("%Y%m%d")
    
    # 내일 날짜 파일만 사용 (히스토리 아카이브는 하지 않음)
    theme_score_map = build_theme_score_map(INPUT_DIR, date=tomorrow_date, archive_history=False)
    
    if theme_score_map:
        print(f"   Theme Score Map 로드: {len(theme_score_map)} 종목")
        # 출처 정보 출력 (상위 3개만)
        top_3 = sorted(
            theme_score_map.items(),
            key=lambda x: x[1]["score"] if isinstance(x[1], dict) else x[1],
            reverse=True
        )[:3]
        for sym, data in top_3:
            sources = data.get("sources", []) if isinstance(data, dict) else []
            if sources:
                print(f"     {sym}: {', '.join(sources[:2])}")
    else:
        print(f"   Theme Score Map: 없음 (input/ 디렉토리 확인)")
    
    # 종목 선정
    print(f"\n🔍 종목 선정 중...")
    result = select_watchlist(
        df,
        cfg=CFG,
        largecap_symbols=LARGECAPS,
        theme_score_map=theme_score_map,
    )
    
    # 결과 출력
    print(f"\n✅ 선정 완료!")
    print(f"\n📊 선정 결과:")
    total = 0
    for category, items in result.items():
        if items:
            print(f"  [{category.upper()}] {len(items)}종목")
            for item in items[:3]:  # 상위 3개만 출력
                symbol = item.get("symbol", "")
                score = item.get("score", 0.0)
                bucket = item.get("bucket", category)
                print(f"    • {symbol} [{bucket}]: {score:.3f}")
            if len(items) > 3:
                print(f"    ... 외 {len(items) - 3}종목")
            total += len(items)
    
    print(f"\n총 {total}종목 선정")
    
    # 내일 날짜로 JSON 저장
    output = {
        "date": tomorrow_str,
        "phase": phase,
        "largecap": result["largecap"],
        "volume": result["volume"],
        "structure": result["structure"],
        "theme": result["theme"],
    }
    
    out_file = OUTPUT_DIR / f"watchlist_{tomorrow_str}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 저장 완료: {out_file}")
    print(f"   내일 정찰봇이 이 파일을 자동으로 읽습니다.")
    print("="*60)


if __name__ == "__main__":
    main()

