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


def get_stock_name_simple(symbol: str) -> str:
    """
    종목명 조회 (간단 버전)
    
    Args:
        symbol: 종목 코드
        
    Returns:
        종목명 (없으면 빈 문자열)
    """
    # TODO: pykrx나 API를 사용하여 종목명 조회
    # 현재는 빈 문자열 반환 (추후 확장 가능)
    try:
        # pykrx 사용 예시 (선택적)
        # from pykrx import stock
        # name = stock.get_market_ticker_name(symbol)
        # return name if name else ""
        return ""
    except Exception:
        return ""


def select_top_3_notification(top_10_candidates: List[Dict]) -> List[Dict]:
    """
    Top 3 알림 종목 선정
    
    기준:
    - 대표성(타입/테마) 우선
    - 점수는 보조 기준
    
    Args:
        top_10_candidates: Top 10 후보군 (전체 정보 포함)
        
    Returns:
        Top 3 알림 종목 리스트 (code/score/type/reason만 포함)
    """
    if len(top_10_candidates) == 0:
        return []
    
    # 타입별로 그룹화
    type_groups = {}
    for item in top_10_candidates:
        item_type = item.get("bucket") or item.get("category", "unknown")
        if item_type not in type_groups:
            type_groups[item_type] = []
        type_groups[item_type].append(item)
    
    # 각 타입에서 최고 점수 종목 선택 (대표성)
    selected = []
    used_types = set()
    
    # 1순위: 각 타입별 최고 점수 종목 (대표성 확보)
    for item_type, items in type_groups.items():
        if item_type not in used_types:
            # 해당 타입에서 최고 점수 종목
            best_item = max(items, key=lambda x: x.get("score", 0.0))
            selected.append(best_item)
            used_types.add(item_type)
            if len(selected) >= 3:
                break
    
    # 2순위: 부족하면 남은 종목 중 점수 높은 순으로 추가
    if len(selected) < 3:
        remaining = [item for item in top_10_candidates if item not in selected]
        remaining.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        selected.extend(remaining[:3 - len(selected)])
    
    # 최종 3개만 반환 (code/score/type/reason만 포함)
    top_3_result = []
    for item in selected[:3]:
        symbol = str(item.get("symbol", "")).zfill(6)
        score = item.get("score", 0.0)
        item_type = item.get("bucket") or item.get("category", "unknown")
        reason_obj = item.get("reason", {})
        if isinstance(reason_obj, dict):
            reason_summary = reason_obj.get("summary") or item.get("selection_reason", "")
        else:
            reason_summary = item.get("selection_reason", "")
        
        top_3_result.append({
            "code": symbol,
            "score": round(score, 4),
            "type": item_type,
            "reason": reason_summary,
        })
    
    return top_3_result


# =========================
# Main
# =========================

def main():
    print("="*60)
    print("📋 문지기봇 - 내일 사용할 종목 선정")
    print("="*60)
    
    # ============================================================
    # STEP 1: 실행 시작 - 오늘 날짜 결정
    # ============================================================
    today = datetime.now()
    today_str = today.strftime("%Y%m%d")
    
    # 내일 날짜 (선정 대상)
    tomorrow = today + timedelta(days=1)
    tomorrow_str = tomorrow.strftime("%Y%m%d")
    
    # 휴장일 체크 (내일 날짜 기준)
    from scout_selector.utils.market_calendar import is_market_open
    
    if not is_market_open(tomorrow_str):
        print("=" * 60)
        print(f"[INFO] Market closed on {tomorrow_str}")
        print(f"[SKIP] Gatekeeper - market closed")
        print("=" * 60)
        sys.exit(0)  # 정상 종료 (오류 아님)
    
    print(f"\n📅 오늘 날짜: {today_str}")
    print(f"📅 내일 날짜 (선정 대상): {tomorrow_str}")
    
    # ============================================================
    # STEP 2: history 디렉터리 생성 (무조건 먼저)
    # ============================================================
    HISTORY_DIR = BASE_DIR / "history" / today_str[:4] / today_str[4:6] / today_str
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n📁 history 디렉터리: {HISTORY_DIR}")
    
    # 종목선정회의(MarketContext) 참고 (없어도 정상 동작)
    market_context = None
    try:
        from scout_selector.market_context import get_or_create_context
        # 오늘 날짜의 MarketContext 참고 (내일 선정을 위한 컨텍스트)
        market_context = get_or_create_context(today_str)
        
        if market_context:
            print(f"\n📋 종목선정회의 참고:")
            print(f"   market_status: {market_context.get('market_status', 'unknown')}")
            if market_context.get('selection_basis'):
                print(f"   selection_basis: {market_context.get('selection_basis')}")
            if market_context.get('exclusion_basis'):
                print(f"   exclusion_basis: {market_context.get('exclusion_basis')}")
    except Exception as e:
        print(f"   ⚠️  종목선정회의 로드 실패 (무시): {e}")
        # MarketContext 없어도 정상 동작 (설계서 v0 - 7장)
    
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
    
    # ============================================================
    # STEP 5: history에 결과 저장 (성공 기준)
    # ============================================================
    from selector import GATEKEEPER_BOT_VERSION
    
    created_at = datetime.now().isoformat()
    
    # candidate_pool.json (Top 10 내부 분석용)
    # STEP 1: 모든 종목을 score 기준으로 정렬하여 상위 10개 추출 (타입 비율 강제하지 않음)
    all_candidates = []
    for category, items in result.items():
        for item in items:
            all_candidates.append({
                **item,
                "category": category,
            })
    
    # score 기준 내림차순 정렬 (타입 비율 강제하지 않음)
    all_candidates.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    top_10_raw = all_candidates[:10]
    
    # STEP 1: candidate_pool.json에는 code/name/type/score/rank/reasons(요약)만 기록
    top_10_candidates = []
    for rank, item in enumerate(top_10_raw, start=1):
        symbol = str(item.get("symbol", "")).zfill(6)
        score = item.get("score", 0.0)
        # type: category 또는 bucket (우선순위: bucket > category)
        item_type = item.get("bucket") or item.get("category", "unknown")
        # reason: reason.summary 또는 selection_reason
        reason_obj = item.get("reason", {})
        if isinstance(reason_obj, dict):
            reason_summary = reason_obj.get("summary") or item.get("selection_reason", "")
        else:
            reason_summary = item.get("selection_reason", "")
        
        # 종목명 조회 (일단 빈 문자열, 추후 확장 가능)
        stock_name = get_stock_name_simple(symbol)
        
        top_10_candidates.append({
            "code": symbol,
            "name": stock_name,
            "type": item_type,
            "score": round(score, 4),
            "rank": rank,
            "reasons": reason_summary,
        })
    
    candidate_pool_output = {
        "meta": {
            "date": today_str,
            "created_at": created_at,
            "bot_name": "문지기봇",
            "bot_version": GATEKEEPER_BOT_VERSION,
            "purpose": "내부 분석용 Top 10 후보군",
        },
        "candidates": top_10_candidates,
    }
    
    # STEP 3: Top 3 알림 종목 선정 (대표성 우선, 점수 보조)
    top_3_notification = select_top_3_notification(top_10_raw)
    
    # Top 3 알림 종목 출력
    if top_3_notification:
        print(f"\n🔔 Top 3 알림 종목 (대표성 우선):")
        for idx, item in enumerate(top_3_notification, 1):
            print(f"  {idx}. {item['code']} [{item['type']}] (점수: {item['score']:.3f})")
            print(f"     → {item['reason']}")
    
    # watchlist.json (정찰봇 전달용 단일 계약 파일)
    # code/name/type/priority/note만 허용 (score 및 상세 판단 정보 제외)
    watchlist_items = []
    
    # priority: largecap=1, volume=2, structure=3, theme=4
    priority_map = {
        "largecap": 1,
        "volume": 2,
        "structure": 3,
        "theme": 4,
    }
    
    for category, items in result.items():
        priority = priority_map.get(category, 5)
        for item in items:
            symbol = str(item.get("symbol", "")).zfill(6)
            stock_name = get_stock_name_simple(symbol)
            item_type = item.get("bucket") or item.get("category", "unknown")
            
            # note: 간단한 메모 (선정 사유 요약)
            reason_obj = item.get("reason", {})
            if isinstance(reason_obj, dict):
                note = reason_obj.get("summary", "") or item.get("selection_reason", "")
            else:
                note = item.get("selection_reason", "")
            
            watchlist_items.append({
                "code": symbol,
                "name": stock_name,
                "type": item_type,
                "priority": priority,
                "note": note,
            })
    
    watchlist_output = {
        "meta": {
            "date": tomorrow_str,
            "created_at": created_at,
            "phase": phase,
            "gatekeeper_version": GATEKEEPER_BOT_VERSION,
            "gatekeeper_bot_version": GATEKEEPER_BOT_VERSION,  # 호환성 유지
        },
        "watchlist": watchlist_items,  # 단일 리스트로 통합 (code/name/type/priority/note만 포함)
    }
    
    # market_context.json (오늘 날짜의 MarketContext)
    market_context_data = None
    try:
        from scout_selector.market_context import get_or_create_context
        market_context_data = get_or_create_context(today_str)
    except Exception as e:
        print(f"   ⚠️  MarketContext 로드 실패: {e}")
        # 기본값으로 생성
        from scout_selector.market_context import create_default_context
        market_context_data = create_default_context(today_str)
    
    # history에 3개 파일 저장
    history_success = True
    history_files = {}
    
    try:
        # 5-1. candidate_pool.json
        candidate_pool_file = HISTORY_DIR / "candidate_pool.json"
        with open(candidate_pool_file, "w", encoding="utf-8") as f:
            json.dump(candidate_pool_output, f, ensure_ascii=False, indent=2)
        history_files["candidate_pool"] = candidate_pool_file
        print(f"\n✅ history 저장: {candidate_pool_file.name}")
        
        # 5-2. market_context.json
        market_context_file = HISTORY_DIR / "market_context.json"
        with open(market_context_file, "w", encoding="utf-8") as f:
            json.dump(market_context_data, f, ensure_ascii=False, indent=2)
        history_files["market_context"] = market_context_file
        print(f"✅ history 저장: {market_context_file.name}")
        
        # 5-3. watchlist.json
        watchlist_file = HISTORY_DIR / "watchlist.json"
        with open(watchlist_file, "w", encoding="utf-8") as f:
            json.dump(watchlist_output, f, ensure_ascii=False, indent=2)
        history_files["watchlist"] = watchlist_file
        print(f"✅ history 저장: {watchlist_file.name}")
        
        # 5-4. manual_additions.json (수동 추가 종목 아카이브)
        try:
            from test.framework.watchlist.manual_additions import archive_manual_additions_to_history
            archive_result = archive_manual_additions_to_history(today_str)
            if archive_result.get("archived", False):
                history_files["manual_additions"] = HISTORY_DIR / "manual_additions.json"
                print(f"✅ history 저장: manual_additions.json (종목 {len(archive_result.get('symbols', []))}개)")
            else:
                print(f"ℹ️  manual_additions 아카이브 없음 (파일 없음)")
        except Exception as e:
            print(f"⚠️  manual_additions 아카이브 실패: {e}")
            # 아카이브 실패해도 파이프라인은 계속 진행
        
    except Exception as e:
        print(f"\n❌ history 저장 실패: {e}")
        import traceback
        traceback.print_exc()
        history_success = False
    
    # ============================================================
    # STEP 6: output 최신 파일 갱신 (조건부 - STEP 5 성공 시에만)
    # ============================================================
    if history_success:
        try:
            # history 파일을 output/_latest.json으로 복사
            import shutil
            
            # watchlist_latest.json
            output_watchlist = OUTPUT_DIR / "watchlist_latest.json"
            shutil.copy2(history_files["watchlist"], output_watchlist)
            print(f"\n✅ output 갱신: {output_watchlist.name}")
            
            # candidate_pool_latest.json
            output_candidate_pool = OUTPUT_DIR / "candidate_pool_latest.json"
            shutil.copy2(history_files["candidate_pool"], output_candidate_pool)
            print(f"✅ output 갱신: {output_candidate_pool.name}")
            
            # market_context_latest.json
            output_market_context = OUTPUT_DIR / "market_context_latest.json"
            shutil.copy2(history_files["market_context"], output_market_context)
            print(f"✅ output 갱신: {output_market_context.name}")
            
            print(f"\n📁 정찰봇이 읽을 파일: {output_watchlist.name}")
            print(f"✅ 문지기봇 종목 선정 완료")
            
        except Exception as e:
            print(f"\n❌ output 갱신 실패: {e}")
            print(f"   ⚠️  history는 저장되었으나 output 갱신 실패")
            print(f"   → 정찰봇은 이전 _latest.json 파일을 사용합니다")
    else:
        print(f"\n⚠️  history 저장 실패로 output 갱신하지 않음")
        print(f"   → 기존 _latest.json 파일 유지")
        print(f"   → 정찰봇은 이전 데이터로 정상 동작합니다")
    
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

