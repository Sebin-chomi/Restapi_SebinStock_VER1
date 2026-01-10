# ===============================
# test/framework/analyzer/daily_report_builder.py
# ===============================
"""
Daily Report Builder

daily_analysis 데이터를 daily_report_schema에 맞게 변환
"""
from datetime import datetime
from typing import Dict, Any, List, Optional

from test.framework.analyzer.daily_report_schema import (
    DailyReport,
    ReportMeta,
    ObserverStats,
    ObserverStockStats,
    CycleSummary,
    CycleOutcomeDistribution,
    RepresentativeCycle,
    ObservationHints,
    PriceZoneSummary,
    PriceZoneStat,
    ManualNotes,
)


def build_daily_report(
    date: str,
    observer_stats: Dict[str, Any],
    scout_version: str = "scout_v1",
    test_mode: bool = True,
    condition_id: Optional[str] = None,
) -> DailyReport:
    """
    observer_stats를 DailyReport 스키마로 변환
    
    Args:
        date: 날짜 (YYYY-MM-DD)
        observer_stats: aggregate_observers() 결과
        scout_version: 정찰봇 버전
        test_mode: 테스트 모드 여부
        condition_id: 조건식 ID
    
    Returns:
        DailyReport 인스턴스
    """
    # [A] ReportMeta
    meta = ReportMeta(
        date=date,
        generated_at=datetime.now(),
        scout_version=scout_version,
        test_mode=test_mode,
        condition_id=condition_id,
    )
    
    # [B] ObserverStats
    by_stock_dict = {}
    for stock_code, stock_data in observer_stats.get("by_stock", {}).items():
        by_stock_dict[stock_code] = ObserverStockStats(
            records=stock_data.get("records", 0),
            observer_triggered_records=stock_data.get("triggered_records", 0),
        )
    
    observer_stats_obj = ObserverStats(
        total_records=observer_stats.get("total_records", 0),
        total_stocks=len(observer_stats.get("by_stock", {})),
        by_stock=by_stock_dict,
    )
    
    # [C] CycleSummary
    obs_summary = observer_stats.get("observer_summary", {})
    cycle_summary = CycleSummary(
        triggered_records=obs_summary.get("triggered_records", 0),
        triggered_cycles=obs_summary.get("triggered_cycles_count", 0),
        open_cycles=obs_summary.get("open_cycles_count", 0),
    )
    
    # [D] CycleOutcomeDistribution
    triggered_cycles = obs_summary.get("triggered_cycle", [])
    outcome_dist = CycleOutcomeDistribution()
    
    for cycle in triggered_cycles:
        exit_type = cycle.get("exit_type", "")
        if exit_type == "reached_1pct":
            outcome_dist.reached_1pct += 1
        elif exit_type == "no_reaction":
            outcome_dist.no_reaction += 1
        elif exit_type == "timeout":
            outcome_dist.timeout += 1
        elif exit_type == "manual_stop":
            outcome_dist.manual_stop += 1
    
    # [E] RepresentativeCycle (최대 2개)
    representative_cycles = []
    cycle_summary_list = obs_summary.get("cycle_summary", [])
    
    for cycle_data in cycle_summary_list[:2]:  # 최대 2개
        try:
            start_time_str = cycle_data.get("start_time", "")
            end_time_str = cycle_data.get("end_time", "")
            
            start_dt = datetime.fromisoformat(
                start_time_str.replace("Z", "+00:00")
            ) if start_time_str else datetime.now()
            
            end_dt = datetime.fromisoformat(
                end_time_str.replace("Z", "+00:00")
            ) if end_time_str else datetime.now()
            
            representative_cycles.append(
                RepresentativeCycle(
                    cycle_id=cycle_data.get("cycle_id", ""),
                    stock=cycle_data.get("stock", ""),
                    start_time=start_dt,
                    end_time=end_dt,
                    duration_sec=cycle_data.get("duration_sec", 0),
                    exit_type=cycle_data.get("exit_type", "unknown"),
                )
            )
        except Exception as e:
            print(f"⚠️  RepresentativeCycle 생성 오류: {e}")
            continue
    
    # [F] ObservationHints
    if triggered_cycles:
        # dominant_exit_type 계산
        exit_type_counts = {}
        total_duration = 0
        valid_durations = 0
        
        for cycle in triggered_cycles:
            exit_type = cycle.get("exit_type", "")
            if exit_type:
                exit_type_counts[exit_type] = (
                    exit_type_counts.get(exit_type, 0) + 1
                )
            
            # duration 계산
            start_dt = cycle.get("start_time")
            end_dt = cycle.get("end_time")
            if start_dt and end_dt:
                try:
                    if isinstance(start_dt, str):
                        start_dt = datetime.fromisoformat(
                            start_dt.replace("Z", "+00:00")
                        )
                    if isinstance(end_dt, str):
                        end_dt = datetime.fromisoformat(
                            end_dt.replace("Z", "+00:00")
                        )
                    duration = (end_dt - start_dt).total_seconds()
                    total_duration += duration
                    valid_durations += 1
                except Exception:
                    pass
        
        dominant_exit_type = None
        if exit_type_counts:
            dominant_exit_type = max(
                exit_type_counts.items(), key=lambda x: x[1]
            )[0]
        
        avg_duration = (
            total_duration / valid_durations
            if valid_durations > 0
            else None
        )
        
        observation_hints = ObservationHints(
            dominant_exit_type=dominant_exit_type,
            avg_cycle_duration_sec=avg_duration,
        )
    else:
        observation_hints = ObservationHints()
    
    # [G] PriceZoneSummary (현재는 빈 상태, 추후 구현)
    price_zone_summary = PriceZoneSummary()
    
    # [H] ManualNotes (빈 상태, 수동 입력용)
    manual_notes = ManualNotes()
    
    # DailyReport 생성
    return DailyReport(
        meta=meta,
        observer_stats=observer_stats_obj,
        cycle_summary=cycle_summary,
        cycle_outcome_distribution=outcome_dist,
        representative_cycles=representative_cycles,
        observation_hints=observation_hints,
        price_zone_summary=price_zone_summary,
        manual_notes=manual_notes,
    )


def save_daily_report(
    report: DailyReport,
    output_dir: str,
) -> str:
    """
    DailyReport를 JSON 파일로 저장
    
    Args:
        report: DailyReport 인스턴스
        output_dir: 출력 디렉토리
    
    Returns:
        저장된 파일 경로
    """
    import json
    import os
    from dataclasses import asdict
    
    os.makedirs(output_dir, exist_ok=True)
    
    # datetime을 ISO 문자열로 변환
    def convert_datetime(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: convert_datetime(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_datetime(item) for item in obj]
        return obj
    
    report_dict = asdict(report)
    report_dict = convert_datetime(report_dict)
    
    file_path = os.path.join(output_dir, "daily_report.json")
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, ensure_ascii=False, indent=2)
    
    return file_path











