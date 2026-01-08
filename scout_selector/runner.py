# ===============================
# gatekeeper_bot/runner.py
# 문지기봇 실행 진입점 (오늘 종목 선정)
# ===============================
"""
문지기봇 실행 스크립트

역할:
- 장 마감 후 배치 프로세스로 실행
- 오늘 날짜 기준으로 종목 선정
- 정찰봇이 사용할 watchlist_YYYYMMDD.json 생성

실행 시점:
- 장 마감 후 (15:30 이후)
- 또는 수동 실행
"""
from __future__ import annotations

import json
from datetime import datetime
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
# Phase Auto Switch
# =========================

def infer_phase(df: pd.DataFrame, lookback: int = 20) -> str:
    """Phase 자동 추론: Cold Start 안정성 보장"""
    if df.empty or "symbol" not in df.columns or "date" not in df.columns:
        # Cold Start: 데이터가 없으면 warmup으로 시작
        return "warmup"
    
    try:
        max_days = (
            df.groupby("symbol")["date"]
            .nunique()
            .max()
        )
        # NaN 체크
        if pd.isna(max_days) or max_days == 0:
            return "warmup"
        return "normal" if max_days >= lookback else "warmup"
    except Exception:
        # 에러 발생 시 안전하게 warmup 반환
        return "warmup"


# =========================
# Load Market Data
# =========================

DATA_FILE = DATA_DIR / "ohlcv_today.csv"
if not DATA_FILE.exists():
    # Cold Start: 데이터 파일이 없으면 빈 DataFrame으로 시작 (warmup phase)
    print(f"⚠️  데이터 파일 없음: {DATA_FILE} → Cold Start 모드 (warmup)")
    df = pd.DataFrame(columns=["symbol", "date", "open", "high", "low", "close", "volume", "turnover_krw"])
else:
    df = pd.read_csv(DATA_FILE)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])

# =========================
# Selector Config
# =========================

phase = infer_phase(df)

CFG = SelectorConfig(
    phase=phase
)

LARGECAPS = ["005930", "000660"]

# =========================
# Theme Score Map 빌드 (표준 입력 경로)
# =========================

from theme_score_builder import build_theme_score_map

INPUT_DIR = BASE_DIR / "input"

# 오늘 날짜
today = datetime.now().strftime("%Y%m%d")

# theme_score_map 빌드 (오늘 날짜만, 과거 파일은 히스토리로 이동)
theme_score_map = build_theme_score_map(INPUT_DIR, date=today, archive_history=True)

if theme_score_map:
    print(f"📊 Theme Score Map 로드 완료: {len(theme_score_map)} 종목")
    # theme_score_map이 {symbol: {score: float, sources: List[str]}} 형태
    top_5 = sorted(
        theme_score_map.items(), 
        key=lambda x: x[1]["score"] if isinstance(x[1], dict) else x[1], 
        reverse=True
    )[:5]
    for sym, data in top_5:
        score = data["score"] if isinstance(data, dict) else data
        sources = data.get("sources", []) if isinstance(data, dict) else []
        sources_str = f" [{', '.join(sources[:2])}]" if sources else ""
        print(f"   {sym}: {score:.2f}{sources_str}")
else:
    print("📊 Theme Score Map: 없음 (input/ 디렉토리 확인)")

# =========================
# Run Selector
# =========================

# Cold Start: 빈 DataFrame이면 최소한의 watchlist 생성
if df.empty:
    print("⚠️  Cold Start: 빈 데이터 → 대형주만 포함")
    result = {
        "largecap": [
            {
                "symbol": s,
                "bucket": "largecap",
                "score": 1.0,
                "reason": {
                    "close": 0.0,
                    "turnover_krw": 0.0,
                }
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

# =========================
# Save Result
# =========================

today = datetime.now().strftime("%Y%m%d")
created_at = datetime.now().isoformat()

# 출력 데이터 계약 준수: 불변 스냅샷 생성
from selector import GATEKEEPER_BOT_VERSION

output = {
    "meta": {
        "date": today,
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

out_file = OUTPUT_DIR / f"watchlist_{today}.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

# latest_watchlist.json 생성 (최신 watchlist를 가리키는 심볼릭 파일)
latest_file = OUTPUT_DIR / "latest_watchlist.json"
with open(latest_file, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("✅ 문지기봇 종목 선정 완료")
print(json.dumps(output, ensure_ascii=False, indent=2))
print(f"📁 저장 위치: {out_file}")
print(f"📁 최신 파일: {latest_file}")
print(f"📋 정찰봇이 이 watchlist를 사용합니다.")

# =========================
# 선정 사유 로그 출력
# =========================

print("\n" + "="*60)
print("📋 선정 종목 및 사유")
print("="*60)

total_count = 0
for category_key, items in output.items():
    if category_key == "meta":
        continue
    
    if items:
        print(f"\n[{category_key.upper()}] {len(items)}종목")
        for item in items:
            symbol = item.get("symbol", "")
            category = item.get("category", item.get("bucket", category_key))
            score = item.get("score", 0.0)
            reason = item.get("reason", {})
            reason_summary = reason.get("summary", "")
            
            # 구조 점수 표시 (구조형만)
            structure_score = item.get("structure_score")
            score_str = f"점수={score:.3f}"
            if structure_score is not None:
                score_str += f" (구조점수={structure_score:.0f}점)"
            
            print(f"  • {symbol} [{category}]: {score_str}")
            if reason_summary:
                print(f"    └─ {reason_summary}")
            total_count += 1

print(f"\n총 {total_count}종목 선정 완료")
print("="*60)
