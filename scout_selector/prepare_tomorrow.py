# ===============================
# gatekeeper_bot/prepare_tomorrow.py
# 문지기봇 실행 진입점 (내일 종목 선정)
# ===============================
"""
문지기봇 내일 종목 선정 스크립트

역할:
- 장 마감 후 배치 프로세스로 실행
- 내일 날짜 기준으로 종목 선정
- 정찰봇이 다음 거래일에 사용할 watchlist_YYYYMMDD.json 생성

실행 시점:
- 장 마감 후 (15:30 이후) 자동 실행 권장
- 또는 수동 실행
"""
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
    
    # 휴장일 체크 (내일 날짜 기준)
    from scout_selector.utils.market_calendar import is_market_open
    
    if not is_market_open(tomorrow_str):
        print("=" * 60)
        print(f"[INFO] Market closed on {tomorrow_str}")
        print(f"[SKIP] Gatekeeper - market closed")
        print("=" * 60)
        sys.exit(0)  # 정상 종료 (오류 아님)
    
    print(f"\n📅 내일 날짜: {tomorrow_str}")
    
    # 데이터 파일 찾기 (어제 또는 오늘 데이터 사용)
    data_files = []
    for days_ago in range(5):  # 최근 5일 데이터 확인
        check_date = datetime.now() - timedelta(days=days_ago)
        check_file = DATA_DIR / f"ohlcv_{check_date.strftime('%Y%m%d')}.csv"
        if check_file.exists():
            data_files.append((check_file, check_date))
    
    if not data_files:
        # Cold Start: 데이터 파일이 없으면 빈 DataFrame으로 시작 (warmup phase)
        print(f"\n⚠️  데이터 파일 없음: {DATA_DIR}/ohlcv_YYYYMMDD.csv")
        print(f"   → Cold Start 모드 (warmup phase)")
        df = pd.DataFrame(columns=["symbol", "date", "open", "high", "low", "close", "volume", "turnover_krw"])
    else:
        # 가장 최근 데이터 사용
        data_file, data_date = data_files[0]
        print(f"\n📊 사용할 데이터: {data_file.name} ({data_date.strftime('%Y-%m-%d')})")
        
        # 데이터 로드
        df = pd.read_csv(data_file)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
        
        print(f"   종목 수: {df['symbol'].nunique()} 종목")
        if not df.empty and "date" in df.columns:
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
    
    # Cold Start: 빈 DataFrame이면 최소한의 watchlist 생성
    if df.empty:
        print("⚠️  Cold Start: 빈 데이터 → 대형주만 포함")
        result = {
            "largecap": [
                {
                    "symbol": s,
                    "category": "largecap",
                    "bucket": "largecap",
                    "score": 1.0,
                    "selection_reason": "Cold Start 모드: 대형주 기본 포함",
                    "reason": {
                        "summary": "Cold Start 모드: 대형주 기본 포함",
                        "close": 0.0,
                        "turnover_krw": 0.0,
                    },
                    "indicators": {},
                }
                for s in LARGECAPS
            ],
            "volume": [],
            "structure": [],
            "theme": [],
        }
    else:
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
    
    # 내일 날짜로 JSON 저장 (출력 데이터 계약 준수)
    from selector import GATEKEEPER_BOT_VERSION
    
    created_at = datetime.now().isoformat()
    
    output = {
        "meta": {
            "date": tomorrow_str,
            "created_at": created_at,
            "phase": phase,
            "gatekeeper_version": GATEKEEPER_BOT_VERSION,  # 출력 메타 필드 (명시적)
            "gatekeeper_bot_version": GATEKEEPER_BOT_VERSION,  # 호환성 유지
        },
        "largecap": result["largecap"],
        "volume": result["volume"],
        "structure": result["structure"],
        "theme": result["theme"],
    }
    
    out_file = OUTPUT_DIR / f"watchlist_{tomorrow_str}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    # latest_watchlist.json 연결 (운영 편의용)
    # 정찰봇은 watchlist_YYYYMMDD.json을 직접 읽는 것을 원칙으로 함
    latest_file = OUTPUT_DIR / "latest_watchlist.json"
    with open(latest_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 저장 완료: {out_file}")
    print(f"📁 최신 파일: {latest_file}")
    print(f"   내일 정찰봇이 {out_file.name} 파일을 자동으로 읽습니다.")
    print(f"   (latest_watchlist.json은 운영 편의용입니다)")
    print(f"✅ 문지기봇 종목 선정 완료")
    print("="*60)


if __name__ == "__main__":
    # 휴장일 체크 (내일 날짜 기준)
    from scout_selector.utils.market_calendar import is_market_open
    
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_str = tomorrow.strftime("%Y%m%d")
    
    if not is_market_open(tomorrow_str):
        print("=" * 60)
        print(f"[INFO] Market closed on {tomorrow_str}")
        print(f"[SKIP] Gatekeeper - market closed")
        print("=" * 60)
        sys.exit(0)  # 정상 종료 (오류 아님)
    
    main()

