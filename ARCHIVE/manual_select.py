# ===============================
# gatekeeper_bot/manual_select.py
# 문지기봇 수동 종목 선정 스크립트
# ===============================
"""
문지기봇 수동 종목 선정

역할:
- 대화형 입력으로 종목 직접 지정
- 각 버킷별로 수동 입력 가능
- 내일 날짜 기준 watchlist_YYYYMMDD.json 생성

사용 시점:
- 자동 선정 결과가 마음에 들지 않을 때
- 특정 종목을 강제로 포함시키고 싶을 때
"""
from __future__ import annotations

import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

from selector import SelectorConfig, compute_features

# =========================
# Paths
# =========================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(exist_ok=True)

# =========================
# Main
# =========================

def main():
    print("="*60)
    print("📋 수동 종목 선정 (내일 사용)")
    print("="*60)
    
    # 내일 날짜
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_str = tomorrow.strftime("%Y%m%d")
    
    print(f"\n📅 내일 날짜: {tomorrow_str}")
    print(f"\n💡 거래량형/구조형/테마형으로 나눠서 각각 2종목씩 입력하세요")
    print(f"   (대형주는 자동으로 포함됩니다)\n")
    
    # 거래량형 종목 입력
    print("📊 [거래량형] 2종목 입력 (예: 035420 051910)")
    volume_input = input("   > ").strip()
    volume_stocks = [s.strip() for s in volume_input.split() if s.strip()][:2]
    
    # 구조형 종목 입력
    print("\n🏗️  [구조형] 2종목 입력 (예: 000270 035720)")
    structure_input = input("   > ").strip()
    structure_stocks = [s.strip() for s in structure_input.split() if s.strip()][:2]
    
    # 테마형 종목 입력
    print("\n🎯 [테마형] 2종목 입력 (예: 005380 006400)")
    theme_input = input("   > ").strip()
    theme_stocks = [s.strip() for s in theme_input.split() if s.strip()][:2]
    
    # 대형주 (고정)
    largecap_stocks = ["005930", "000660"]
    
    # 실제 데이터 로드 (가능한 경우)
    latest_data = {}
    try:
        # 최근 데이터 파일 찾기
        data_files = []
        for days_ago in range(5):
            check_date = datetime.now() - timedelta(days=days_ago)
            check_file = DATA_DIR / f"ohlcv_{check_date.strftime('%Y%m%d')}.csv"
            if check_file.exists():
                data_files.append((check_file, check_date))
                break
        
        if data_files:
            data_file, _ = data_files[0]
            df = pd.read_csv(data_file)
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])
            
            # Feature 계산
            cfg = SelectorConfig(phase="warmup")
            df_feat = compute_features(df, cfg)
            latest = df_feat.sort_values(["symbol", "date"]).groupby("symbol").tail(1).set_index("symbol")
            
            # 각 종목의 최신 데이터 저장
            for symbol in latest.index:
                latest_data[symbol] = latest.loc[symbol]
            
            print(f"📊 데이터 로드 완료: {len(latest_data)} 종목")
    except Exception as e:
        print(f"⚠️  데이터 로드 실패 (계속 진행): {e}")
    
    # 결과 구성 (bucket별 reason 구조화)
    def make_item(symbol: str, bucket: str, score: float = 0.8):
        reason = {}
        
        # 실제 데이터가 있으면 사용
        if symbol in latest_data:
            row = latest_data[symbol]
            
            if bucket == "largecap":
                reason = {
                    "close": float(row.get("close", 0)),
                    "turnover_krw": float(row.get("turnover_krw", 0)),
                }
            elif bucket == "volume":
                reason = {
                    "turnover_krw": float(row.get("turnover_krw", 0)),
                    "vol_spike_ratio": float(row.get("vol_spike_ratio", 0)),
                    "hlc_volatility": float(row.get("hlc_volatility", 0)),
                }
            elif bucket == "structure":
                reason = {
                    "trend": float(row.get("trend", 0)),
                    "clean": float(row.get("clean", 0)),
                    "hlc_volatility": float(row.get("hlc_volatility", 0)),
                }
            elif bucket == "theme":
                reason = {
                    "theme_score": 0.0,  # 수동 입력이므로 테마 점수 없음
                    "turnover_krw": float(row.get("turnover_krw", 0)),
                }
        else:
            # 데이터가 없으면 수동 입력 표시
            if bucket == "largecap":
                reason = {
                    "close": 0.0,
                    "turnover_krw": 0.0,
                }
            elif bucket == "volume":
                reason = {
                    "turnover_krw": 0.0,
                    "vol_spike_ratio": 0.0,
                    "hlc_volatility": 0.0,
                }
            elif bucket == "structure":
                reason = {
                    "trend": 0.0,
                    "clean": 0.0,
                    "hlc_volatility": 0.0,
                }
            elif bucket == "theme":
                reason = {
                    "theme_score": 0.0,
                    "turnover_krw": 0.0,
                }
        
        return {
            "symbol": symbol,
            "bucket": bucket,
            "score": score,
            "reason": reason,
        }
    
    result = {
        "largecap": [make_item(s, "largecap", 1.0) for s in largecap_stocks],
        "volume": [make_item(s, "volume") for s in volume_stocks],
        "structure": [make_item(s, "structure") for s in structure_stocks],
        "theme": [make_item(s, "theme") for s in theme_stocks],
    }
    
    # 결과 출력
    print(f"\n✅ 선정 완료!")
    print(f"\n📊 선정 결과:")
    total = 0
    for category, items in result.items():
        if items:
            symbols = [item["symbol"] for item in items]
            print(f"  [{category.upper()}] {len(items)}종목: {', '.join(symbols)}")
            total += len(items)
    
    print(f"\n총 {total}종목 선정")
    
    # 확인
    print(f"\n❓ 이대로 저장하시겠습니까? (y/n)")
    try:
        confirm = input("   > ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n❌ 취소되었습니다.")
        return
    
    if confirm != 'y':
        print("❌ 취소되었습니다.")
        return
    
    # JSON 저장 (출력 데이터 계약 준수)
    try:
        from selector import GATEKEEPER_BOT_VERSION
        from datetime import datetime
        
        created_at = datetime.now().isoformat()
        
        output = {
            "meta": {
                "date": tomorrow_str,
                "created_at": created_at,
                "phase": "warmup",  # 수동 선정은 warmup
                "gatekeeper_version": GATEKEEPER_BOT_VERSION,  # 출력 메타 필드 (명시적)
                "gatekeeper_bot_version": GATEKEEPER_BOT_VERSION,  # 호환성 유지
            },
            "largecap": result["largecap"],
            "volume": result["volume"],
            "structure": result["structure"],
            "theme": result["theme"],
        }
        
        out_file = OUTPUT_DIR / f"watchlist_{tomorrow_str}.json"
        
        # 디렉토리 확인
        if not OUTPUT_DIR.exists():
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            print(f"📁 디렉토리 생성: {OUTPUT_DIR}")
        
        # 파일 저장
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        # 파일 존재 확인
        if out_file.exists():
            print(f"\n✅ 저장 완료: {out_file}")
            print(f"   파일 크기: {out_file.stat().st_size} bytes")
            print(f"   내일 정찰봇이 이 파일을 자동으로 읽습니다.")
        else:
            print(f"\n❌ 저장 실패: 파일이 생성되지 않았습니다.")
            print(f"   경로: {out_file}")
        
    except Exception as e:
        print(f"\n❌ 저장 중 오류 발생: {e}")
        print(f"   경로: {out_file}")
        import traceback
        traceback.print_exc()
    
    print("="*60)


if __name__ == "__main__":
    main()

