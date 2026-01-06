# ===============================
# test/framework/analyzer/daily_report_schema.py
# ===============================
"""
Daily Report Schema (v1)

이 파일은 **데이터 저장용이 아니라 "계약(contract)"**이다.

보고서 생성기, 그래프 생성기, 전략 분석기, 딥러닝 전처리
👉 모두가 이 스키마를 신뢰하게 만드는 게 목적
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


# ===============================
# [A] 메타 영역 – 보고서 정체성
# ===============================
@dataclass
class ReportMeta:
    """
    보고서 메타 정보
    
    절대 해석 없음
    "이 보고서는 어떤 맥락에서 만들어졌는가"
    """
    date: str                    # YYYY-MM-DD
    generated_at: datetime       # 보고서 생성 시각
    scout_version: str           # 정찰봇 버전
    test_mode: bool              # 테스트 여부
    condition_id: Optional[str] = None  # 조건식 ID (없을 수 있음)


# ===============================
# [B] Observer 실행 통계 (record 기준)
# ===============================
@dataclass
class ObserverStockStats:
    """
    종목별 Observer 통계
    
    record = 사실의 최소 단위
    cycle과 의도적으로 분리
    """
    records: int                         # observer 실행 횟수
    observer_triggered_records: int     # triggered=True record 수


@dataclass
class ObserverStats:
    """Observer 실행 통계"""
    total_records: int
    total_stocks: int
    by_stock: Dict[str, ObserverStockStats] = field(default_factory=dict)


# ===============================
# [C] Cycle 요약 통계 (핵심)
# ===============================
@dataclass
class CycleSummary:
    """
    Cycle 요약 통계
    
    여기서부터 사건 단위
    triggered_cycles의 의미가 명확해짐
    """
    triggered_records: int      # record 단위 triggered 수
    triggered_cycles: int       # 종료된 cycle 수
    open_cycles: int            # 미종료 cycle 수


# ===============================
# [D] Cycle 결과 분포
# ===============================
@dataclass
class CycleOutcomeDistribution:
    """
    Cycle 결과 분포
    
    "좋다/나쁘다" 없음
    종료 이유의 분포만 기록
    """
    reached_1pct: int = 0
    no_reaction: int = 0
    timeout: int = 0
    manual_stop: int = 0


# ===============================
# [E] 대표 Cycle 요약 (최대 2개)
# ===============================
@dataclass
class RepresentativeCycle:
    """
    대표 Cycle 요약
    
    가격 ❌
    수익 ❌
    구조 재현용
    """
    cycle_id: str
    stock: str
    start_time: datetime
    end_time: datetime
    duration_sec: int
    exit_type: str


# ===============================
# [F] 반복 관측 힌트 (통계 요약만)
# ===============================
@dataclass
class ObservationHints:
    """
    반복 관측 힌트
    
    "왜 그런지" ❌
    "그랬다" ✅
    """
    dominant_exit_type: Optional[str] = None
    avg_cycle_duration_sec: Optional[float] = None


# ===============================
# [G] 가격 구간 통계 (지지·저항 후보)
# ===============================
@dataclass
class PriceZoneStat:
    """가격 구간 통계"""
    price_zone: str            # 예: "72000-72500"
    exit_count: int
    no_reaction_count: int


@dataclass
class PriceZoneSummary:
    """
    가격 구간 요약
    
    선 긋기 ❌
    후보 데이터만
    """
    zones: List[PriceZoneStat] = field(default_factory=list)


# ===============================
# [H] 사람 입력 영역 (완전 분리)
# ===============================
@dataclass
class ManualNotes:
    """
    사람 입력 영역
    
    자동 생성 ❌
    수정 가능
    의미/해석 전용 공간
    """
    market_one_liner: Optional[str] = None
    confusing_cycle_id: Optional[str] = None
    unnecessary_action_note: Optional[str] = None
    free_memo: Optional[str] = None


# ===============================
# [I] Daily Report (전체)
# ===============================
@dataclass
class DailyReport:
    """
    Daily Report 전체 구조
    
    모든 컴포넌트를 포함하는 최상위 스키마
    """
    meta: ReportMeta
    observer_stats: ObserverStats
    cycle_summary: CycleSummary
    cycle_outcome_distribution: CycleOutcomeDistribution
    representative_cycles: List[RepresentativeCycle] = field(default_factory=list)
    observation_hints: ObservationHints = field(default_factory=ObservationHints)
    price_zone_summary: PriceZoneSummary = field(default_factory=PriceZoneSummary)
    manual_notes: ManualNotes = field(default_factory=ManualNotes)




