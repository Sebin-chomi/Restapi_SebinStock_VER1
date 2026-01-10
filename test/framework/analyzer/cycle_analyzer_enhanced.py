# ===============================
# test/framework/analyzer/cycle_analyzer_enhanced.py
# Daily Cycle Analysis 보강 v1
# ===============================
"""
Cycle 분석 확장 모듈

설계서 v1에 따른 보강 기능:
- 타임아웃 종료 세분화
- 통계 보강 (중앙값, 표준편차, 최소/최대)
- 종목/슬롯별 비교
- Cycle 정보량 점수 (info_score)
- 데이터 품질 자동 경고 및 제외 처리
- 시장 메모 자동 생성
"""
import statistics
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict


# ===============================
# 설정값 (Config)
# ===============================
NEAR_TARGET_THRESHOLD = 0.7  # NEAR_TARGET_TIMEOUT 판정 기준 (%)
INFO_SCORE_WEIGHTS = {
    "event_count": 0.3,
    "amplitude_pct": 0.3,
    "max_return_pct": 0.4,
}
QUALITY_MULTIPLIERS = {
    "PASS": 1.0,
    "WARN": 0.7,
    "FAIL": 0.0,
}


# ===============================
# 1. 데이터 품질 판정
# ===============================
def assess_data_quality(cycle: Dict[str, Any], cycle_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Cycle 데이터 품질 판정
    
    Args:
        cycle: cycle 정보
        cycle_records: cycle에 포함된 모든 record
        
    Returns:
        {"status": "PASS|WARN|FAIL", "reasons": [...]}
    """
    reasons = []
    status = "PASS"
    
    # 핵심 필드 체크
    has_price = False
    has_volume = False
    has_turnover = False
    has_observer = False
    
    price_count = 0
    volume_count = 0
    turnover_count = 0
    observer_count = 0
    
    for rec in cycle_records:
        snapshot = rec.get("snapshot", {})
        observer = rec.get("observer", {})
        
        # 가격 체크 (OHLC 중 하나라도 있으면 OK)
        if snapshot.get("current_price") is not None:
            has_price = True
            price_count += 1
        
        # 거래량 체크
        if snapshot.get("volume") is not None and snapshot.get("volume", 0) > 0:
            has_volume = True
            volume_count += 1
        
        # 거래대금 체크
        if snapshot.get("turnover_krw") is not None and snapshot.get("turnover_krw", 0) > 0:
            has_turnover = True
            turnover_count += 1
        
        # Observer 체크
        if observer:
            has_observer = True
            observer_count += 1
    
    # FAIL 판정
    if not has_price:
        reasons.append("가격 데이터 없음")
        status = "FAIL"
    if not has_volume:
        reasons.append("거래량 데이터 없음")
        status = "FAIL"
    if not has_turnover:
        reasons.append("거래대금 데이터 없음")
        status = "FAIL"
    if not has_observer:
        reasons.append("Observer 데이터 없음")
        status = "FAIL"
    
    # WARN 판정 (일부만 있거나 0 값이 많음)
    if status == "PASS":
        total_records = len(cycle_records)
        if total_records > 0:
            price_ratio = price_count / total_records
            volume_ratio = volume_count / total_records
            turnover_ratio = turnover_count / total_records
            
            if price_ratio < 0.8:
                reasons.append(f"가격 데이터 비율 낮음 ({price_ratio:.1%})")
                status = "WARN"
            if volume_ratio < 0.5:
                reasons.append(f"거래량 데이터 비율 낮음 ({volume_ratio:.1%})")
                status = "WARN"
            if turnover_ratio < 0.5:
                reasons.append(f"거래대금 데이터 비율 낮음 ({turnover_ratio:.1%})")
                status = "WARN"
    
    return {
        "status": status,
        "reasons": reasons,
    }


# ===============================
# 2. Cycle 가격 정보 추출
# ===============================
def extract_cycle_price_info(cycle: Dict[str, Any], cycle_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Cycle의 가격 정보 추출 (max_return, min_return, amplitude)
    
    Args:
        cycle: cycle 정보
        cycle_records: cycle에 포함된 모든 record
        
    Returns:
        {
            "max_return_pct": float,
            "min_return_pct": float,
            "amplitude_pct": float,
            "start_price": float,
            "end_price": float,
        }
    """
    prices = []
    start_price = None
    end_price = None
    
    for rec in cycle_records:
        snapshot = rec.get("snapshot", {})
        price = snapshot.get("current_price")
        if price is not None and price > 0:
            prices.append(price)
    
    if not prices:
        return {
            "max_return_pct": 0.0,
            "min_return_pct": 0.0,
            "amplitude_pct": 0.0,
            "start_price": None,
            "end_price": None,
        }
    
    start_price = prices[0]
    end_price = prices[-1]
    max_price = max(prices)
    min_price = min(prices)
    
    # 수익률 계산
    if start_price and start_price > 0:
        max_return_pct = ((max_price - start_price) / start_price) * 100
        min_return_pct = ((min_price - start_price) / start_price) * 100
        amplitude_pct = ((max_price - min_price) / start_price) * 100
    else:
        max_return_pct = 0.0
        min_return_pct = 0.0
        amplitude_pct = 0.0
    
    return {
        "max_return_pct": round(max_return_pct, 2),
        "min_return_pct": round(min_return_pct, 2),
        "amplitude_pct": round(amplitude_pct, 2),
        "start_price": start_price,
        "end_price": end_price,
    }


# ===============================
# 3. Observer 이벤트 카운트
# ===============================
def count_observer_events(cycle_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Cycle 내 Observer 변화 이벤트 카운트
    
    Args:
        cycle_records: cycle에 포함된 모든 record
        
    Returns:
        {
            "event_count": int,
            "observer_changes": {
                "volume": int,
                "box": int,
                "base_candle": int,
            }
        }
    """
    event_count = 0
    observer_changes = {
        "volume": 0,
        "box": 0,
        "base_candle": 0,
    }
    
    prev_observer = {}
    
    for rec in cycle_records:
        observer = rec.get("observer", {})
        box = rec.get("box", {})
        base_candle = rec.get("base_candle", {})
        
        # Volume 변화 체크 (triggered 상태 변화)
        if observer.get("triggered") != prev_observer.get("triggered"):
            observer_changes["volume"] += 1
            event_count += 1
        
        # Box 변화 체크
        box_formed = box.get("formed", False)
        prev_box_formed = prev_observer.get("box_formed", False)
        if box_formed != prev_box_formed:
            observer_changes["box"] += 1
            event_count += 1
        
        # Base Candle 변화 체크
        base_exists = base_candle.get("exists", False)
        prev_base_exists = prev_observer.get("base_exists", False)
        if base_exists != prev_base_exists:
            observer_changes["base_candle"] += 1
            event_count += 1
        
        # 이전 상태 저장
        prev_observer = {
            "triggered": observer.get("triggered", False),
            "box_formed": box_formed,
            "base_exists": base_exists,
        }
    
    return {
        "event_count": event_count,
        "observer_changes": observer_changes,
    }


# ===============================
# 4. 타임아웃 서브타입 분류
# ===============================
def classify_timeout_subtype(
    cycle: Dict[str, Any],
    price_info: Dict[str, Any],
    event_info: Dict[str, Any],
) -> str:
    """
    TIMEOUT인 경우 서브타입 분류
    
    Args:
        cycle: cycle 정보
        price_info: extract_cycle_price_info 결과
        event_info: count_observer_events 결과
        
    Returns:
        "NO_EVENT_TIMEOUT" | "LOW_SIGNAL_TIMEOUT" | "NEAR_TARGET_TIMEOUT" | "N/A"
    """
    exit_type = cycle.get("exit_type", "")
    
    if exit_type != "timeout":
        return "N/A"
    
    event_count = event_info.get("event_count", 0)
    max_return_pct = price_info.get("max_return_pct", 0.0)
    amplitude_pct = price_info.get("amplitude_pct", 0.0)
    
    # NO_EVENT_TIMEOUT: 이벤트 없고 가격 반응도 낮음
    if event_count == 0 and max_return_pct < 0.5 and amplitude_pct < 0.5:
        return "NO_EVENT_TIMEOUT"
    
    # NEAR_TARGET_TIMEOUT: 목표는 미도달이지만 임계치 이상
    if max_return_pct >= NEAR_TARGET_THRESHOLD:
        return "NEAR_TARGET_TIMEOUT"
    
    # LOW_SIGNAL_TIMEOUT: 이벤트는 있으나 가격 반응이 작음
    if event_count > 0 and max_return_pct < 0.5:
        return "LOW_SIGNAL_TIMEOUT"
    
    # 기본값
    return "LOW_SIGNAL_TIMEOUT"


# ===============================
# 5. 정보량 점수 산출
# ===============================
def calculate_info_score(
    cycle: Dict[str, Any],
    price_info: Dict[str, Any],
    event_info: Dict[str, Any],
    data_quality: Dict[str, Any],
) -> float:
    """
    Cycle 정보량 점수 산출 (0~100)
    
    Args:
        cycle: cycle 정보
        price_info: extract_cycle_price_info 결과
        event_info: count_observer_events 결과
        data_quality: assess_data_quality 결과
        
    Returns:
        info_score (0.0 ~ 100.0)
    """
    event_count = event_info.get("event_count", 0)
    amplitude_pct = abs(price_info.get("amplitude_pct", 0.0))
    max_return_pct = abs(price_info.get("max_return_pct", 0.0))
    
    # 정규화 (임의의 최대값 기준)
    norm_event = min(event_count / 10.0, 1.0)  # 최대 10개 이벤트 = 1.0
    norm_amplitude = min(amplitude_pct / 5.0, 1.0)  # 최대 5% = 1.0
    norm_max_return = min(max_return_pct / 3.0, 1.0)  # 최대 3% = 1.0
    
    # 가중 합산
    score = (
        INFO_SCORE_WEIGHTS["event_count"] * norm_event * 100 +
        INFO_SCORE_WEIGHTS["amplitude_pct"] * norm_amplitude * 100 +
        INFO_SCORE_WEIGHTS["max_return_pct"] * norm_max_return * 100
    )
    
    # 데이터 품질 페널티
    quality_status = data_quality.get("status", "PASS")
    multiplier = QUALITY_MULTIPLIERS.get(quality_status, 1.0)
    score *= multiplier
    
    return round(score, 2)


# ===============================
# 6. 슬롯 타입 추출
# ===============================
def get_slot_type(symbol: str, watchlist_data: Optional[Dict[str, Any]] = None) -> str:
    """
    종목의 슬롯 타입 추출
    
    Args:
        symbol: 종목 코드
        watchlist_data: watchlist JSON 데이터 (선택)
        
    Returns:
        "benchmark" | "volume" | "structure" | "theme" | "unknown"
    """
    if not watchlist_data:
        return "unknown"
    
    # largecap (benchmark)
    for item in watchlist_data.get("largecap", []):
        if isinstance(item, dict):
            if str(item.get("symbol", "")).zfill(6) == str(symbol).zfill(6):
                return "benchmark"
        elif str(item).zfill(6) == str(symbol).zfill(6):
            return "benchmark"
    
    # volume
    for item in watchlist_data.get("volume", []):
        if isinstance(item, dict):
            if str(item.get("symbol", "")).zfill(6) == str(symbol).zfill(6):
                return "volume"
        elif str(item).zfill(6) == str(symbol).zfill(6):
            return "volume"
    
    # structure
    for item in watchlist_data.get("structure", []):
        if isinstance(item, dict):
            if str(item.get("symbol", "")).zfill(6) == str(symbol).zfill(6):
                return "structure"
        elif str(item).zfill(6) == str(symbol).zfill(6):
            return "structure"
    
    # theme
    for item in watchlist_data.get("theme", []):
        if isinstance(item, dict):
            if str(item.get("symbol", "")).zfill(6) == str(symbol).zfill(6):
                return "theme"
        elif str(item).zfill(6) == str(symbol).zfill(6):
            return "theme"
    
    return "unknown"


# ===============================
# 7. Cycle 확장 분석 (메인 함수)
# ===============================
def enhance_cycle_analysis(
    cycles: List[Dict[str, Any]],
    all_records: List[Dict[str, Any]],
    watchlist_data: Optional[Dict[str, Any]] = None,
    exclude_fail: bool = True,
) -> Dict[str, Any]:
    """
    Cycle 분석 확장 (설계서 v1)
    
    Args:
        cycles: 기존 cycle 목록
        all_records: 모든 record (cycle과 매칭용)
        watchlist_data: watchlist JSON 데이터 (슬롯 타입 추출용)
        exclude_fail: FAIL 품질 cycle 제외 여부
        
    Returns:
        확장된 cycle 분석 결과
    """
    enhanced_cycles = []
    fail_cycles = []
    
    # record를 cycle_id로 그룹화
    records_by_cycle = defaultdict(list)
    for rec in all_records:
        meta = rec.get("meta", {})
        stock_code = meta.get("stock_code", "")
        timestamp_str = meta.get("timestamp", "")
        
        # cycle과 매칭 (start_time ~ end_time 사이)
        for cycle in cycles:
            if cycle.get("stock") == stock_code:
                start_time_str = cycle.get("start_time", "")
                end_time_str = cycle.get("end_time", "")
                
                try:
                    if start_time_str and end_time_str and timestamp_str:
                        rec_dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                        start_dt = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
                        end_dt = datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))
                        
                        if start_dt <= rec_dt <= end_dt:
                            cycle_id = cycle.get("cycle_id", "")
                            records_by_cycle[cycle_id].append(rec)
                except Exception:
                    pass
    
    # 각 cycle 확장 분석
    for cycle in cycles:
        cycle_id = cycle.get("cycle_id", "")
        cycle_records = records_by_cycle.get(cycle_id, [])
        
        # 데이터 품질 판정
        data_quality = assess_data_quality(cycle, cycle_records)
        
        # FAIL 제외 옵션
        if exclude_fail and data_quality["status"] == "FAIL":
            fail_cycles.append(cycle_id)
            continue
        
        # 가격 정보 추출
        price_info = extract_cycle_price_info(cycle, cycle_records)
        
        # Observer 이벤트 카운트
        event_info = count_observer_events(cycle_records)
        
        # 타임아웃 서브타입 분류
        timeout_subtype = classify_timeout_subtype(cycle, price_info, event_info)
        
        # 정보량 점수 산출
        info_score = calculate_info_score(cycle, price_info, event_info, data_quality)
        
        # 슬롯 타입 추출
        slot_type = get_slot_type(cycle.get("stock", ""), watchlist_data)
        
        # 확장된 cycle 정보
        enhanced_cycle = {
            **cycle,
            "slot_type": slot_type,
            "timeout_subtype": timeout_subtype,
            "max_return_pct": price_info["max_return_pct"],
            "min_return_pct": price_info["min_return_pct"],
            "amplitude_pct": price_info["amplitude_pct"],
            "event_count": event_info["event_count"],
            "observer_changes": event_info["observer_changes"],
            "data_quality": data_quality,
            "info_score": info_score,
        }
        
        # duration_min 추가 (초 -> 분)
        duration_sec = cycle.get("duration_sec", 0)
        enhanced_cycle["duration_min"] = round(duration_sec / 60.0, 2)
        
        enhanced_cycles.append(enhanced_cycle)
    
    return {
        "enhanced_cycles": enhanced_cycles,
        "fail_cycles_count": len(fail_cycles),
        "fail_cycle_ids": fail_cycles,
    }


# ===============================
# 8. 통계 보강 (중앙값, 표준편차, 최소/최대)
# ===============================
def calculate_enhanced_statistics(enhanced_cycles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Cycle 통계 보강 (평균, 중앙값, 표준편차, 최소/최대)
    
    Args:
        enhanced_cycles: 확장된 cycle 목록
        
    Returns:
        통계 딕셔너리
    """
    if not enhanced_cycles:
        return {
            "duration": {},
            "info_score": {},
            "max_return_pct": {},
            "amplitude_pct": {},
        }
    
    durations = [c.get("duration_min", 0) for c in enhanced_cycles if c.get("duration_min") is not None]
    info_scores = [c.get("info_score", 0) for c in enhanced_cycles if c.get("info_score") is not None]
    max_returns = [c.get("max_return_pct", 0) for c in enhanced_cycles if c.get("max_return_pct") is not None]
    amplitudes = [c.get("amplitude_pct", 0) for c in enhanced_cycles if c.get("amplitude_pct") is not None]
    
    def calc_stats(values: List[float]) -> Dict[str, float]:
        if not values:
            return {}
        
        return {
            "mean": round(statistics.mean(values), 2),
            "median": round(statistics.median(values), 2),
            "std": round(statistics.stdev(values), 2) if len(values) > 1 else 0.0,
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "count": len(values),
        }
    
    return {
        "duration": calc_stats(durations),
        "info_score": calc_stats(info_scores),
        "max_return_pct": calc_stats(max_returns),
        "amplitude_pct": calc_stats(amplitudes),
    }


# ===============================
# 9. 종목별/슬롯별 요약
# ===============================
def generate_summary_by_group(enhanced_cycles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    종목별/슬롯별 요약 생성
    
    Args:
        enhanced_cycles: 확장된 cycle 목록
        
    Returns:
        {
            "by_stock": {...},
            "by_slot": {...},
        }
    """
    by_stock = defaultdict(lambda: {
        "cycle_count": 0,
        "avg_duration": 0.0,
        "avg_info_score": 0.0,
        "no_event_timeout_ratio": 0.0,
        "durations": [],
        "info_scores": [],
        "no_event_count": 0,
    })
    
    by_slot = defaultdict(lambda: {
        "cycle_count": 0,
        "avg_duration": 0.0,
        "avg_info_score": 0.0,
        "no_event_timeout_ratio": 0.0,
        "durations": [],
        "info_scores": [],
        "no_event_count": 0,
    })
    
    for cycle in enhanced_cycles:
        stock = cycle.get("stock", "unknown")
        slot = cycle.get("slot_type", "unknown")
        duration = cycle.get("duration_min", 0)
        info_score = cycle.get("info_score", 0)
        timeout_subtype = cycle.get("timeout_subtype", "")
        
        # 종목별
        by_stock[stock]["cycle_count"] += 1
        by_stock[stock]["durations"].append(duration)
        by_stock[stock]["info_scores"].append(info_score)
        if timeout_subtype == "NO_EVENT_TIMEOUT":
            by_stock[stock]["no_event_count"] += 1
        
        # 슬롯별
        by_slot[slot]["cycle_count"] += 1
        by_slot[slot]["durations"].append(duration)
        by_slot[slot]["info_scores"].append(info_score)
        if timeout_subtype == "NO_EVENT_TIMEOUT":
            by_slot[slot]["no_event_count"] += 1
    
    # 평균 계산
    for stock_data in by_stock.values():
        if stock_data["durations"]:
            stock_data["avg_duration"] = round(statistics.mean(stock_data["durations"]), 2)
        if stock_data["info_scores"]:
            stock_data["avg_info_score"] = round(statistics.mean(stock_data["info_scores"]), 2)
        if stock_data["cycle_count"] > 0:
            stock_data["no_event_timeout_ratio"] = round(
                stock_data["no_event_count"] / stock_data["cycle_count"], 2
            )
    
    for slot_data in by_slot.values():
        if slot_data["durations"]:
            slot_data["avg_duration"] = round(statistics.mean(slot_data["durations"]), 2)
        if slot_data["info_scores"]:
            slot_data["avg_info_score"] = round(statistics.mean(slot_data["info_scores"]), 2)
        if slot_data["cycle_count"] > 0:
            slot_data["no_event_timeout_ratio"] = round(
                slot_data["no_event_count"] / slot_data["cycle_count"], 2
            )
    
    return {
        "by_stock": dict(by_stock),
        "by_slot": dict(by_slot),
    }


# ===============================
# 10. 시장 메모 자동 생성
# ===============================
def generate_market_memo(enhanced_cycles: List[Dict[str, Any]]) -> str:
    """
    시장 메모 자동 생성 (1줄)
    
    Args:
        enhanced_cycles: 확장된 cycle 목록
        
    Returns:
        시장 메모 문자열
    """
    if not enhanced_cycles:
        return "데이터 없음"
    
    total_cycles = len(enhanced_cycles)
    timeout_cycles = [c for c in enhanced_cycles if c.get("exit_type") == "timeout"]
    timeout_count = len(timeout_cycles)
    
    if timeout_count == 0:
        return "타임아웃 없음"
    
    # 타임아웃 서브타입 분포
    no_event_count = sum(1 for c in timeout_cycles if c.get("timeout_subtype") == "NO_EVENT_TIMEOUT")
    near_target_count = sum(1 for c in timeout_cycles if c.get("timeout_subtype") == "NEAR_TARGET_TIMEOUT")
    low_signal_count = sum(1 for c in timeout_cycles if c.get("timeout_subtype") == "LOW_SIGNAL_TIMEOUT")
    
    # 평균 amplitude
    avg_amplitude = statistics.mean([c.get("amplitude_pct", 0) for c in enhanced_cycles]) if enhanced_cycles else 0
    
    # 평균 event_count
    avg_event_count = statistics.mean([c.get("event_count", 0) for c in enhanced_cycles]) if enhanced_cycles else 0
    
    # 메모 생성 규칙
    if no_event_count / timeout_count > 0.5 and avg_amplitude < 1.0:
        return "방향성 약하고 신호 희박"
    
    if near_target_count > 0:
        return "추세 시도 있었으나 목표 미도달"
    
    if avg_event_count > 3 and avg_amplitude < 1.0:
        return "신호는 잦았으나 가격 반응 약함(노이즈 가능)"
    
    if avg_amplitude > 2.0:
        return "가격 변동성 높음"
    
    return "정상 범위"

