# ===============================
# test/framework/analyzer/post_market_analyzer.py
# ===============================
"""
Post-Market Analyzer

정찰봇이 수집한 JSONL 기록을 분석하여:
- Observer/Reason 집계
- 시장 성격 요약 생성
- 일일 평가 기록 저장
"""
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import defaultdict, Counter
from pathlib import Path


# ===============================
# 경로 설정
# ===============================
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../..")
)
SCOUT_RECORDS_DIR = os.path.join(PROJECT_ROOT, "records", "scout")
ANALYSIS_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "records", "analysis")
os.makedirs(ANALYSIS_OUTPUT_DIR, exist_ok=True)


# ===============================
# 제외할 날짜 목록 (테스트/비정상 데이터)
# ===============================
EXCLUDED_DATES = {
    "2026-01-05",  # 테스트 데이터 제외
    "2026-01-06",  # 테스트 데이터 제외
}

# 첫 정상 데이터 날짜
FIRST_VALID_DATE = "2026-01-07"


# ===============================
# JSONL 읽기
# ===============================
def load_scout_records(date: str) -> List[Dict[str, Any]]:
    """특정 날짜의 모든 정찰 기록 로드"""
    # ✅ 제외된 날짜는 빈 리스트 반환
    if date in EXCLUDED_DATES:
        msg = f"  ⚠️  {date}는 분석에서 제외된 날짜입니다 (테스트 데이터)"
        print(msg)
        return []
    
    date_dir = os.path.join(SCOUT_RECORDS_DIR, date)
    
    if not os.path.exists(date_dir):
        return []
    
    all_records = []
    
    # 모든 .jsonl 파일 읽기
    for file_path in Path(date_dir).glob("*.jsonl"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        all_records.append(record)
                    except json.JSONDecodeError as e:
                        print(f"⚠️  JSON 파싱 오류 ({file_path}): {e}")
        except Exception as e:
            print(f"⚠️  파일 읽기 오류 ({file_path}): {e}")
    
    return all_records


# ===============================
# Observer/Reason 집계
# ===============================
def aggregate_observers(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Observer 결과 집계 (Cycle 판정 포함)
    
    용어 정의:
    - record: observer가 한 번 실행된 로그
    - trigger: 관측 조건을 만족한 '사건'
    - cycle: 트리거 이후 유지, 종료까지의 묶음
        * 시작: observer.triggered == True (이전 cycle 종료 후 첫 trigger)
        * 종료: outcome.exit_type 존재 (v1 허용: reached_1pct, no_reaction, timeout, manual_stop)
        * 종목별로 동시에 1개만 존재 (상태 머신: IDLE/ACTIVE)
    
    exit_type 판정 기준:
    - exit_type은 반드시 하나만
    - 숫자보다 이벤트 기준
    - 성과/성공/실패 용어 금지
    - v1 허용 exit_type: reached_1pct, no_reaction, timeout, manual_stop
    """
    from datetime import datetime
    
    stats = {
        "total_records": len(records),
        "by_stock": defaultdict(lambda: {
            "records": 0,
            "triggered_records": 0,
            "box_formed": 0,
            "base_candle_exists": 0,
        }),
        "observer_summary": {
            "triggered_records": 0,
            "triggered_stocks": set(),
            "triggers": [],
            "triggered_cycle": [],  # 완전히 종료된 cycle 목록
            "open_cycles_count": 0,  # 장 종료 시점 미종료 cycle 수
        },
        "box_summary": {
            "formed_count": 0,
            "formed_stocks": set(),
        },
        "base_candle_summary": {
            "exists_count": 0,
            "exists_stocks": set(),
        },
        "session_distribution": Counter(),
        "no_event_reasons": Counter(),
    }
    
    # ============================================================
    # exit_type 판정 기준 (v1 고정)
    # ============================================================
    # 대원칙:
    # 1. exit_type은 반드시 하나만
    # 2. 숫자보다 이벤트 기준
    # 3. 성과/성공/실패 용어 금지
    #    - "잘 됐냐?" ❌
    #    - "어떤 이유로 관측이 끝났냐?" ✅
    #
    # v1에서 허용하는 exit_type (고정, 변경 불가):
    VALID_EXIT_TYPES = {
        "reached_1pct",    # 기준 반응 폭 도달
        "no_reaction",    # 관측 시간 동안 의미 있는 반응 없음
        "timeout",        # 최대 관측 시간 초과
        "manual_stop",    # 시스템/테스트 종료
    }
    # ❗ 이 4개 외에는 v1에 넣지 않는다
    
    # ============================================================
    # exit_type 판정 우선순위 (v1 고정)
    # ============================================================
    # 같은 record에서 여러 조건이 동시에 만족될 수 있으므로
    # 우선순위가 필수
    #
    # v1 우선순위 (고정):
    EXIT_TYPE_PRIORITY = [
        "manual_stop",   # 1순위: 사람이 멈추면 그게 최우선
        "reached_1pct",  # 2순위: 반응 도달은 가장 명확한 종료
        "timeout",       # 3순위: timeout은 시스템 조건
        "no_reaction",   # 4순위: no_reaction은 "나머지"
    ]
    
    def select_exit_type(exit_types) -> Optional[str]:
        """
        exit_type 우선순위에 따라 하나 선택
        
        Args:
            exit_types: exit_type 문자열, 리스트, 또는 None
        
        Returns:
            우선순위에 따라 선택된 exit_type (문자열) 또는 None
        """
        if not exit_types:
            return None
        
        # 리스트인 경우
        if isinstance(exit_types, list):
            exit_type_list = exit_types
        # 문자열인 경우
        elif isinstance(exit_types, str):
            exit_type_list = [exit_types]
        else:
            return None
        
        # 유효한 exit_type만 필터링
        valid_types = [
            et for et in exit_type_list
            if isinstance(et, str) and et in VALID_EXIT_TYPES
        ]
        
        if not valid_types:
            return None
        
        # 우선순위에 따라 첫 번째 선택
        for priority_type in EXIT_TYPE_PRIORITY:
            if priority_type in valid_types:
                return priority_type
        
        # 우선순위에 없으면 첫 번째 유효한 타입 반환
        return valid_types[0]
    
    # ============================================================
    # 1. record를 시간순으로 정렬 (필수)
    # ============================================================
    def get_timestamp(rec: Dict[str, Any]) -> datetime:
        """record에서 timestamp 추출 및 변환"""
        ts_str = rec.get("meta", {}).get("timestamp", "")
        if not ts_str:
            return datetime.min
        
        try:
            if isinstance(ts_str, str):
                # ISO 형식 파싱
                if "T" in ts_str:
                    return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                else:
                    return datetime.min
            return ts_str
        except Exception:
            return datetime.min
    
    sorted_records = sorted(records, key=get_timestamp)
    
    # ============================================================
    # 2. Cycle 상태 머신 (종목별 IDLE/ACTIVE)
    # ============================================================
    open_cycles: Dict[str, Dict[str, Any]] = {}  # stock_code -> active cycle
    
    # ============================================================
    # 3. record 순회 (시간순)
    # ============================================================
    for rec_idx, rec in enumerate(sorted_records):
        meta = rec.get("meta", {})
        stock_code = meta.get("stock_code", "UNKNOWN")
        session = meta.get("session", "UNKNOWN")
        timestamp_str = meta.get("timestamp", "")
        
        # timestamp를 datetime 객체로 변환
        try:
            if timestamp_str:
                timestamp_dt = datetime.fromisoformat(
                    timestamp_str.replace("Z", "+00:00")
                )
            else:
                timestamp_dt = None
        except Exception:
            timestamp_dt = None
        
        # record: observer가 한 번 실행된 로그
        stats["by_stock"][stock_code]["records"] += 1
        stats["session_distribution"][session] += 1
        
        # trigger: 관측 조건을 만족한 '사건'
        observer = rec.get("observer", {})
        is_triggered = observer.get("triggered", False)
        
        if is_triggered:
            stats["observer_summary"]["triggered_records"] += 1
            stats["observer_summary"]["triggered_stocks"].add(stock_code)
            stats["by_stock"][stock_code]["triggered_records"] += 1
            
            if timestamp_str:
                # trigger 정보 저장
                stats["observer_summary"]["triggers"].append({
                    "stock": stock_code,
                    "time": timestamp_str,
                    "session": session,
                    "record_index": rec_idx,
                })
        
        # ============================================================
        # 4. Cycle 시작 판정 (IDLE -> ACTIVE)
        # ============================================================
        if stock_code not in open_cycles:
            # 상태: IDLE
            if is_triggered:
                # cycle START
                open_cycles[stock_code] = {
                    "stock": stock_code,
                    "start_time": timestamp_dt if timestamp_dt else None,
                    "start_time_str": timestamp_str,
                    "start_record_index": rec_idx,
                    "start_session": session,
                    "trigger_type": "observer_triggered",
                    "records_in_cycle": 1,
                }
        else:
            # 상태: ACTIVE
            # cycle이 열려있으면 record 수 증가
            open_cycles[stock_code]["records_in_cycle"] += 1
        
        # ============================================================
        # 5. Cycle 종료 판정 (ACTIVE -> IDLE)
        # ============================================================
        if stock_code in open_cycles:
            outcome = rec.get("outcome", {})
            raw_exit_type = outcome.get("exit_type")
            
            # exit_type 우선순위에 따라 선택
            exit_type = select_exit_type(raw_exit_type)
            
            # exit_type 검증 및 처리
            if exit_type:
                # 유효한 exit_type: cycle 종료
                cycle = open_cycles[stock_code]
                # datetime 객체는 문자열로 저장 (JSON 직렬화를 위해)
                cycle["end_time"] = timestamp_dt if timestamp_dt else None
                cycle["end_time_str"] = timestamp_str
                cycle["end_record_index"] = rec_idx
                cycle["end_session"] = session
                cycle["exit_type"] = exit_type
                
                # 완전히 종료된 cycle을 triggered_cycle에 추가
                # datetime 객체를 문자열로 변환하여 저장
                cycle_copy = cycle.copy()
                if cycle_copy.get("start_time"):
                    if isinstance(cycle_copy["start_time"], datetime):
                        cycle_copy["start_time"] = (
                            cycle_copy["start_time"].isoformat()
                        )
                if cycle_copy.get("end_time"):
                    if isinstance(cycle_copy["end_time"], datetime):
                        cycle_copy["end_time"] = (
                            cycle_copy["end_time"].isoformat()
                        )
                stats["observer_summary"]["triggered_cycle"].append(
                    cycle_copy
                )
                
                # active_cycles에서 제거 (IDLE로 전환)
                del open_cycles[stock_code]
            elif raw_exit_type:
                # exit_type이 있지만 유효하지 않음: 경고 로그
                print(
                    f"⚠️  잘못된 exit_type: {raw_exit_type} "
                    f"(종목: {stock_code}, record_index: {rec_idx})"
                )
                print(
                    f"    허용되는 exit_type: {VALID_EXIT_TYPES}"
                )
                # 잘못된 exit_type은 무시하고 cycle은 계속 진행
        
        # Box 집계
        box = rec.get("box", {})
        if box.get("formed", False):
            stats["box_summary"]["formed_count"] += 1
            stats["box_summary"]["formed_stocks"].add(stock_code)
            stats["by_stock"][stock_code]["box_formed"] += 1
        
        # Base Candle 집계
        base_candle = rec.get("base_candle", {})
        if base_candle.get("exists", False):
            stats["base_candle_summary"]["exists_count"] += 1
            stats["base_candle_summary"]["exists_stocks"].add(stock_code)
            stats["by_stock"][stock_code]["base_candle_exists"] += 1
        
        # 이벤트 미발생 사유 집계
        no_event_reasons = rec.get("no_event_reason", [])
        for reason in no_event_reasons:
            stats["no_event_reasons"][reason] += 1
    
    # ============================================================
    # 6. 장 종료 시 미종료 cycle 처리
    # ============================================================
    # 마지막 record의 timestamp를 장 종료 시각으로 사용
    market_close_time = None
    if sorted_records:
        last_rec = sorted_records[-1]
        last_ts_str = last_rec.get("meta", {}).get("timestamp", "")
        if last_ts_str:
            try:
                market_close_time = datetime.fromisoformat(
                    last_ts_str.replace("Z", "+00:00")
                )
            except Exception:
                pass
    
    for stock_code, cycle in open_cycles.items():
        # 미종료 cycle을 timeout으로 종료 처리
        cycle["end_time"] = market_close_time
        cycle["end_time_str"] = last_ts_str if last_ts_str else ""
        cycle["exit_type"] = "timeout"
        cycle["end_reason"] = "session_end"
        
        # 미종료 cycle도 triggered_cycle에 추가 (정책 선택)
        stats["observer_summary"]["triggered_cycle"].append(cycle.copy())
    
    # ============================================================
    # 7. Cycle 요약 생성 (구조 정보만)
    # ============================================================
    summary_cycles = []
    date_str = sorted_records[0].get("meta", {}).get("date", "") if sorted_records else ""
    
    for i, cycle in enumerate(stats["observer_summary"]["triggered_cycle"], start=1):
        # start_time과 end_time이 datetime 또는 문자열일 수 있음
        start_dt = cycle.get("start_time")
        end_dt = cycle.get("end_time")
        
        # 문자열인 경우 datetime으로 변환
        if isinstance(start_dt, str):
            try:
                start_dt = datetime.fromisoformat(
                    start_dt.replace("Z", "+00:00")
                )
            except Exception:
                start_dt = None
        if isinstance(end_dt, str):
            try:
                end_dt = datetime.fromisoformat(
                    end_dt.replace("Z", "+00:00")
                )
            except Exception:
                end_dt = None
        
        duration_sec = 0
        if start_dt and end_dt:
            try:
                duration_sec = int((end_dt - start_dt).total_seconds())
            except Exception:
                pass
        
        # start_time_str과 end_time_str 우선 사용, 없으면 datetime을 문자열로 변환
        start_time_str = cycle.get("start_time_str", "")
        if not start_time_str and start_dt:
            start_time_str = start_dt.isoformat()
        
        end_time_str = cycle.get("end_time_str", "")
        if not end_time_str and end_dt:
            end_time_str = end_dt.isoformat()
        
        summary_cycles.append({
            "cycle_id": f"{date_str}-{cycle['stock']}-{i:02d}",
            "stock": cycle["stock"],
            "start_time": start_time_str,
            "end_time": end_time_str,
            "duration_sec": duration_sec,
            "exit_type": cycle.get("exit_type", "unknown"),
        })
    
    # 요약을 observer_summary에 추가
    stats["observer_summary"]["cycle_summary"] = summary_cycles
    
    # ============================================================
    # 8. 최종 통계 계산
    # ============================================================
    stats["observer_summary"]["triggered_cycles_count"] = len(
        stats["observer_summary"]["triggered_cycle"]
    )
    stats["observer_summary"]["open_cycles_count"] = len(open_cycles)
    
    # set을 list로 변환 (JSON 직렬화를 위해)
    stats["observer_summary"]["triggered_stocks"] = list(
        stats["observer_summary"]["triggered_stocks"]
    )
    stats["box_summary"]["formed_stocks"] = list(
        stats["box_summary"]["formed_stocks"]
    )
    stats["base_candle_summary"]["exists_stocks"] = list(
        stats["base_candle_summary"]["exists_stocks"]
    )
    stats["session_distribution"] = dict(stats["session_distribution"])
    stats["no_event_reasons"] = dict(stats["no_event_reasons"])
    
    return stats


def aggregate_reasons(
    date: str,
    records: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Reason 집계 (watchlist 선정 사유)"""
    # watchlist JSON 파일 읽기
    watchlist_path = os.path.join(
        PROJECT_ROOT,
        "scout_selector",
        "output",
        f"watchlist_{date.replace('-', '')}.json"
    )
    
    reason_stats = {
        "by_bucket": defaultdict(lambda: {
            "count": 0,
            "stocks": [],
            "avg_score": 0.0,
        }),
        "top_reasons": [],
        "watchlist_loaded": False,
    }
    
    if not os.path.exists(watchlist_path):
        return reason_stats
    
    try:
        with open(watchlist_path, "r", encoding="utf-8") as f:
            watchlist_data = json.load(f)
        
        reason_stats["watchlist_loaded"] = True
        
        # 각 버킷별 reason 집계
        for bucket in ["largecap", "volume", "structure", "theme"]:
            stocks = watchlist_data.get(bucket, [])
            if not isinstance(stocks, list):
                continue
            
            scores = []
            for stock in stocks:
                if isinstance(stock, dict):
                    symbol = stock.get("symbol", "")
                    score = stock.get("score", 0.0)
                    reason = stock.get("reason", {})
                    
                    reason_stats["by_bucket"][bucket]["stocks"].append({
                        "symbol": symbol,
                        "score": score,
                        "reason": reason,
                    })
                    scores.append(score)
                elif isinstance(stock, str):
                    # 구버전 호환 (튜플 형식)
                    reason_stats["by_bucket"][bucket]["stocks"].append({
                        "symbol": stock,
                        "score": 0.0,
                        "reason": {},
                    })
            
            reason_stats["by_bucket"][bucket]["count"] = len(stocks)
            if scores:
                reason_stats["by_bucket"][bucket]["avg_score"] = (
                    sum(scores) / len(scores)
                )
        
        # dict를 일반 dict로 변환 (JSON 직렬화를 위해)
        reason_stats["by_bucket"] = dict(reason_stats["by_bucket"])
        for bucket in reason_stats["by_bucket"]:
            reason_stats["by_bucket"][bucket] = dict(
                reason_stats["by_bucket"][bucket]
            )
        
    except Exception as e:
        print(f"⚠️  Watchlist 읽기 오류: {e}")
    
    return reason_stats


# ===============================
# 상위 100 결과 읽기 (선택)
# ===============================
def load_top_100_results(date: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    상위 100 결과 읽기 (선택 기능)
    
    TODO: 실제 상위 100 결과 파일 경로를 확인해야 함
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    # 예시: daily_scan 결과를 읽는다고 가정
    top_100_path = os.path.join(
        PROJECT_ROOT,
        "test",
        "daily_scan",
        "output",
        f"top_100_{date.replace('-', '')}.csv"
    )
    
    if not os.path.exists(top_100_path):
        return []
    
    # CSV 읽기 (간단한 구현)
    results = []
    try:
        import csv
        with open(top_100_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                results.append(row)
    except Exception as e:
        print(f"⚠️  상위 100 결과 읽기 오류: {e}")
    
    return results


# ===============================
# 시장 성격 요약 생성
# ===============================
def generate_market_character_summary(
    observer_stats: Dict[str, Any],
    records: List[Dict[str, Any]],
    top_100_results: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """시장 성격 요약 생성"""
    
    total_records = len(records)
    triggered_records = observer_stats["observer_summary"]["triggered_records"]
    box_formed = observer_stats["box_summary"]["formed_count"]
    
    # 기본 통계
    trigger_rate = (
        triggered_records / total_records * 100
        if total_records > 0
        else 0
    )
    box_rate = (
        box_formed / total_records * 100
        if total_records > 0
        else 0
    )
    
    # 시장 성격 판단
    market_character = {
        "date": records[0]["meta"]["date"] if records else "",
        "total_scouts": total_records,
        "trigger_rate": round(trigger_rate, 2),
        "box_rate": round(box_rate, 2),
        "active_stocks": len(observer_stats["observer_summary"]["triggered_stocks"]),
        "session_distribution": observer_stats["session_distribution"],
        "character": "UNKNOWN",
        "description": "",
    }
    
    # 시장 성격 분류
    if trigger_rate >= 20:
        market_character["character"] = "ACTIVE"
        market_character["description"] = (
            "활발한 시장: Observer 트리거 비율이 높음. "
            "기회가 많은 날로 판단됨."
        )
    elif trigger_rate >= 10:
        market_character["character"] = "MODERATE"
        market_character["description"] = (
            "보통 시장: 적당한 기회가 있었던 날."
        )
    elif trigger_rate >= 5:
        market_character["character"] = "QUIET"
        market_character["description"] = (
            "조용한 시장: 기회가 적었던 날."
        )
    else:
        market_character["character"] = "DEAD"
        market_character["description"] = (
            "침체 시장: 거의 기회가 없었던 날."
        )
    
    # Box 형성 비율 추가 분석
    if box_rate >= 30:
        market_character["description"] += (
            " Box 형성 비율이 높아 패턴 형성이 활발함."
        )
    elif box_rate < 10:
        market_character["description"] += (
            " Box 형성 비율이 낮아 패턴 형성이 부족함."
        )
    
    return market_character


# ===============================
# 일일 평가 기록 저장
# ===============================
def save_daily_analysis(
    date: str,
    observer_stats: Dict[str, Any],
    market_character: Dict[str, Any],
    reason_stats: Optional[Dict[str, Any]] = None,
    top_100_results: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, str]:
    """일일 평가 기록 저장"""
    
    date_dir = os.path.join(ANALYSIS_OUTPUT_DIR, date)
    os.makedirs(date_dir, exist_ok=True)
    
    # JSON 저장
    json_path = os.path.join(date_dir, "daily_analysis.json")
    
    # datetime 객체를 문자열로 변환하는 헬퍼 함수
    def convert_datetime_for_json(obj):
        """datetime 객체를 ISO 문자열로 변환"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: convert_datetime_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_datetime_for_json(item) for item in obj]
        elif isinstance(obj, set):
            return list(obj)  # set을 list로 변환
        return obj
    
    analysis_data = {
        "date": date,
        "generated_at": datetime.now().isoformat(),
        "observer_stats": convert_datetime_for_json(observer_stats),
        "reason_stats": reason_stats or {},
        "market_character": market_character,
        "top_100_available": top_100_results is not None and len(top_100_results) > 0,
    }
    
    if top_100_results:
        analysis_data["top_100_count"] = len(top_100_results)
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(analysis_data, f, ensure_ascii=False, indent=2)
    
    # TXT 요약 저장 (사람용)
    txt_path = os.path.join(date_dir, "daily_analysis.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write(f"일일 시장 분석 요약 - {date}\n")
        f.write("=" * 60 + "\n\n")
        
        f.write("📊 기본 통계\n")
        f.write(f"  총 정찰 횟수 (total_records): {observer_stats['total_records']}\n")
        f.write(f"  관찰 종목 수: {len(observer_stats['by_stock'])}\n")
        f.write(f"  Triggered Records: {observer_stats['observer_summary']['triggered_records']}회\n")
        cycles_count = observer_stats['observer_summary'].get(
            'triggered_cycles_count', 0
        )
        open_count = observer_stats['observer_summary'].get(
            'open_cycles_count', 0
        )
        f.write(f"  완전히 종료된 Cycles: {cycles_count}개\n")
        if open_count > 0:
            f.write(f"  장 종료 시 미종료 Cycles: {open_count}개\n")
        f.write(f"  Box 형성: {observer_stats['box_summary']['formed_count']}회\n")
        f.write(f"  Base Candle 존재: {observer_stats['base_candle_summary']['exists_count']}회\n\n")
        
        f.write("📈 시장 성격\n")
        f.write(f"  분류: {market_character['character']}\n")
        f.write(f"  트리거 비율: {market_character['trigger_rate']}%\n")
        f.write(f"  Box 비율: {market_character['box_rate']}%\n")
        f.write(f"  활성 종목 수: {market_character['active_stocks']}\n")
        f.write(f"  설명: {market_character['description']}\n\n")
        
        f.write("⏰ 세션 분포\n")
        for session, count in market_character['session_distribution'].items():
            f.write(f"  {session}: {count}회\n")
        
        if observer_stats['no_event_reasons']:
            f.write("\n❌ 이벤트 미발생 사유\n")
            for reason, count in sorted(
                observer_stats['no_event_reasons'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]:
                f.write(f"  {reason}: {count}회\n")
        
        if observer_stats['observer_summary']['triggers']:
            f.write("\n🎯 Observer 트리거 (Trigger Events)\n")
            for trigger in observer_stats['observer_summary']['triggers'][:20]:
                f.write(
                    f"  {trigger['stock']} - "
                    f"{trigger['time']} ({trigger['session']})\n"
                )
        
        # Cycle 요약 정보 (구조 정보만)
        cycle_summary = observer_stats['observer_summary'].get(
            'cycle_summary', []
        )
        if cycle_summary:
            f.write("\n🔄 Cycle 요약 (구조 정보)\n")
            f.write(f"  총 {len(cycle_summary)}개\n\n")
            for cycle in cycle_summary[:20]:
                f.write(f"  Cycle ID: {cycle['cycle_id']}\n")
                f.write(f"    종목: {cycle['stock']}\n")
                f.write(f"    시작: {cycle['start_time']}\n")
                f.write(f"    종료: {cycle['end_time']}\n")
                f.write(f"    지속 시간: {cycle['duration_sec']}초\n")
                f.write(f"    종료 사유: {cycle['exit_type']}\n")
                f.write("\n")
        
        if reason_stats and reason_stats.get('watchlist_loaded'):
            f.write("\n📋 Watchlist 선정 사유\n")
            for bucket, data in reason_stats['by_bucket'].items():
                f.write(f"  {bucket}: {data['count']}종목 (평균 점수: {data['avg_score']:.2f})\n")
    
    return {
        "json_path": json_path,
        "txt_path": txt_path,
    }


# ===============================
# 메인 분석 함수
# ===============================
def analyze_daily_market(
    date: Optional[str] = None,
    include_top_100: bool = False,
    with_graphs: bool = False,
) -> Dict[str, Any]:
    """
    일일 시장 분석 실행
    
    Args:
        date: 분석할 날짜 (YYYY-MM-DD), None이면 오늘
        include_top_100: 상위 100 결과 포함 여부
    
    Returns:
        분석 결과 딕셔너리
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    print(f"📊 일일 시장 분석 시작: {date}")
    
    # ✅ 제외된 날짜 확인
    if date in EXCLUDED_DATES:
        msg = f"  ⚠️  {date}는 분석에서 제외된 날짜입니다 (테스트 데이터)"
        print(msg)
        excluded_msg = (
            f"{date}는 분석에서 제외된 날짜입니다 (테스트 데이터). "
            f"첫 정상 데이터 날짜: {FIRST_VALID_DATE}"
        )
        return {
            "date": date,
            "error": "excluded_date",
            "message": excluded_msg,
            "excluded": True,
            "first_valid_date": FIRST_VALID_DATE,
        }
    
    # 1. 정찰 기록 로드
    print("  📂 정찰 기록 로드 중...")
    records = load_scout_records(date)
    
    if not records:
        print(f"  ⚠️  {date}의 정찰 기록이 없습니다.")
        return {
            "date": date,
            "error": "no_records",
            "message": f"{date}의 정찰 기록이 없습니다.",
        }
    
    print(f"  ✅ {len(records)}개의 기록 로드 완료")
    
    # 2. Observer/Reason 집계
    print("  📈 Observer/Reason 집계 중...")
    observer_stats = aggregate_observers(records)
    reason_stats = aggregate_reasons(date, records)
    
    # 3. 상위 100 결과 읽기 (선택)
    top_100_results = None
    if include_top_100:
        print("  📊 상위 100 결과 읽기 중...")
        top_100_results = load_top_100_results(date)
        if top_100_results:
            print(f"  ✅ {len(top_100_results)}개 결과 로드 완료")
    
    # 4. 시장 성격 요약 생성
    print("  🎯 시장 성격 요약 생성 중...")
    market_character = generate_market_character_summary(
        observer_stats,
        records,
        top_100_results,
    )
    
    # 5. 일일 평가 기록 저장
    print("  💾 일일 평가 기록 저장 중...")
    saved_paths = save_daily_analysis(
        date,
        observer_stats,
        market_character,
        reason_stats,
        top_100_results,
    )
    
    # 6. Daily Report 스키마 생성 (계약용)
    print("  📋 Daily Report 스키마 생성 중...")
    try:
        from test.framework.analyzer.daily_report_builder import (
            build_daily_report,
            save_daily_report,
        )
        
        daily_report = build_daily_report(
            date=date,
            observer_stats=observer_stats,
            scout_version="scout_v1",
            test_mode=True,
        )
        
        date_dir = os.path.join(ANALYSIS_OUTPUT_DIR, date)
        report_path = save_daily_report(daily_report, date_dir)
        print(f"     Report: {report_path}")
        
        # 7. 그래프 생성 (선택적)
        graphs_dir = None
        if with_graphs:
            print("  📊 그래프 생성 중...")
            try:
                from test.framework.analyzer.graph_generator import (
                    generate_daily_graphs,
                )
                
                graphs_dir = os.path.join(date_dir, "daily_graphs")
                graph_results = generate_daily_graphs(report_path, graphs_dir)
                
                if any(graph_results.values()):
                    print(f"     Graphs: {graphs_dir}")
                else:
                    print("  ⚠️  그래프가 생성되지 않았습니다.")
            except Exception as e:
                print(f"  ⚠️  그래프 생성 오류: {e}")
                graphs_dir = None
    except Exception as e:
        print(f"  ⚠️  Daily Report 생성 오류: {e}")
        report_path = None
        graphs_dir = None
    
    print("  ✅ 저장 완료:")
    print(f"     JSON: {saved_paths['json_path']}")
    print(f"     TXT:  {saved_paths['txt_path']}")
    if report_path:
        print(f"     Report: {report_path}")
        saved_paths["report_path"] = report_path
    if graphs_dir:
        print(f"     Graphs: {graphs_dir}")
        saved_paths["graphs_dir"] = graphs_dir
    
    return {
        "date": date,
        "total_records": len(records),
        "observer_stats": observer_stats,
        "market_character": market_character,
        "saved_paths": saved_paths,
    }


if __name__ == "__main__":
    import sys
    
    date = None
    include_top_100 = False
    
    if len(sys.argv) > 1:
        date = sys.argv[1]
    if len(sys.argv) > 2 and sys.argv[2] == "--top100":
        include_top_100 = True
    
    result = analyze_daily_market(date, include_top_100)
    
    if "error" in result:
        print(f"\n❌ 오류: {result['message']}")
        sys.exit(1)
    
    print("\n✅ 분석 완료!")

