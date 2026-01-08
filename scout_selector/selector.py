from __future__ import annotations

# ===============================
# gatekeeper_bot/selector.py
# 문지기봇 핵심 엔진
# ===============================

# 문지기봇 버전
GATEKEEPER_BOT_VERSION = "1.0.0"
"""
문지기봇 핵심 선정 엔진

역할:
- 장 마감 후 1일 1회 실행되는 독립 배치 봇
- 전 종목 대상 입구 필터 및 1·2차 필터링 수행
- 정찰봇이 감시할 종목 후보군 생성

처리 흐름:
1. 입구 필터 (Gate Filter)
   - 거래량 = 0 제외
   - 거래대금 < 25억 원 제외
   - 관리종목/거래정지/상장폐지 예정 제외
   - 필수 데이터 결손 제외

2. 1차 필터 (Primary Filter) - OR 조건
   - 거래량 스파이크 >= 1.8 OR
   - 거래대금 >= 50억 OR
   - 일중 변동성 >= 3.0%
   - 출력 규모 관리: 최소 30, 권장 80, 최대 120종목

3. 2차 필터 (Secondary Filter)
   - 버킷별 점수 계산 (거래량형, 구조형, 테마형)
   - 각 버킷별 할당량에 맞춰 상위 종목 선정
   - 최종 후보군 출력 (5~6종목)

제약사항:
- 매수/매도 판단 금지
- 장 중 재선정 금지
- 실시간 데이터 사용 금지
- 주문/계좌 접근 금지
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
import math
import pandas as pd

# =========================
# Config
# =========================

@dataclass(frozen=True)
class SelectionQuota:
    volume: int = 2
    structure: int = 2
    theme: int = 2
    largecap: int = 2
    
    # 구조형 후보 유지 기준
    structure_min_score: int = 60  # 60점 이상 우선
    structure_candidate_min: int = 8  # 최소 8종목
    structure_candidate_max: int = 12  # 최대 12종목
    
    # 최종 후보군 압축
    final_target_min: int = 5
    final_target_max: int = 6
    max_per_category: int = 3  # 단일 카테고리 3종목 초과 금지


@dataclass(frozen=True)
class SelectorConfig:
    phase: str = "warmup"  # "warmup" | "normal"
    quota: SelectionQuota = SelectionQuota()

    # 입구 필터 (Gate Filter)
    gate_filter_min_turnover_krw: float = 2.5e9  # 25억 원
    gate_filter_min_price: float = 500.0
    
    # 1차 필터 (Primary Filter) - OR 조건
    primary_filter_vol_spike_min: float = 1.8  # 거래량 스파이크 >= 1.8
    primary_filter_min_turnover_krw: float = 5e9  # 거래대금 >= 50억
    primary_filter_min_volatility: float = 0.03  # 일중 변동성 >= 3.0%
    
    # 1차 필터 출력 규모 관리
    primary_filter_output_min: int = 30  # 최소 30종목
    primary_filter_output_target: int = 80  # 권장 80종목
    primary_filter_output_max: int = 120  # 최대 120종목
    
    # 2차 필터 (기존 파라미터)
    min_price: float = 500.0
    min_turnover_krw: float = 2e9
    min_avg_vol_20: float = 50_000

    vol_spike_ratio_min: float = 2.0
    intraday_volatility_min: float = 0.03

    struct_trend_days: int = 5
    struct_range_min: float = 0.02
    struct_range_max: float = 0.10

    theme_min_score: float = 0.4

    w_turnover: float = 0.35
    w_vol_spike: float = 0.35
    w_volatility: float = 0.30

    w_trend: float = 0.45
    w_cleanliness: float = 0.30
    w_reasonable_range: float = 0.25

    w_theme: float = 0.70
    w_theme_turnover: float = 0.30


# =========================
# Helpers
# =========================

def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _z_norm(series: pd.Series) -> pd.Series:
    std = series.std(ddof=0)
    if std == 0 or math.isnan(std):
        return pd.Series(0.0, index=series.index)
    return (series - series.mean()) / std


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


# =========================
# Features
# =========================

def compute_features(df: pd.DataFrame, cfg: SelectorConfig, lookback: int = 20) -> pd.DataFrame:
    df = df.sort_values(["symbol", "date"]).copy()

    df["vol_avg"] = df.groupby("symbol")["volume"].transform(
        lambda s: s.rolling(lookback, min_periods=1).mean()
    )

    # 일중 변동성: (고가 - 저가) ÷ 시가 (설계 기준)
    df["intraday_volatility"] = (df["high"] - df["low"]) / df["open"].replace(0, pd.NA)
    # 기존 호환성 유지 (종가 기준)
    df["hlc_volatility"] = (df["high"] - df["low"]) / df["close"].replace(0, pd.NA)

    df["vol_spike_ratio"] = (
        df["volume"] / df["vol_avg"].replace(0, pd.NA)
    ).fillna(1.0)

    N = cfg.struct_trend_days
    df["trend"] = df.groupby("symbol")["close"].transform(
        lambda s: s.pct_change(N).fillna(0.0)
    )

    # 이동평균 계산 (단/중/장기)
    df["ma5"] = df.groupby("symbol")["close"].transform(
        lambda s: s.rolling(5, min_periods=1).mean()
    )
    df["ma20"] = df.groupby("symbol")["close"].transform(
        lambda s: s.rolling(20, min_periods=1).mean()
    )
    df["ma60"] = df.groupby("symbol")["close"].transform(
        lambda s: s.rolling(60, min_periods=1).mean()
    )
    
    # MA 기울기 (전일 대비 변화율)
    df["ma5_slope"] = df.groupby("symbol")["ma5"].transform(
        lambda s: s.pct_change(1).fillna(0.0)
    )
    df["ma20_slope"] = df.groupby("symbol")["ma20"].transform(
        lambda s: s.pct_change(1).fillna(0.0)
    )
    
    # MA 밀집도 (MA 간 거리)
    df["ma_spread"] = (
        (df["ma5"] - df["ma20"]).abs() / df["close"].replace(0, pd.NA)
    ).fillna(0.0)
    
    df["above_ma5"] = (df["close"] > df["ma5"]).astype(int)
    df["clean"] = df.groupby("symbol")["above_ma5"].transform(
        lambda s: s.rolling(5, min_periods=1).mean().fillna(0.5)
    )
    
    # 고점/저점 구조 (Higher Low, 고점 갱신)
    df["higher_low"] = df.groupby("symbol")["low"].transform(
        lambda s: (s > s.shift(1)).fillna(False).astype(int)
    )
    df["new_high"] = df.groupby("symbol")["high"].transform(
        lambda s: (s >= s.rolling(20, min_periods=1).max()).fillna(False).astype(int)
    )
    
    # 장대 음봉 체크 (전일 대비 하락률 > 5%)
    df["big_red_candle"] = df.groupby("symbol")["close"].transform(
        lambda s: (s.pct_change(1) < -0.05).fillna(False).astype(int)
    )
    
    # 단기 과열 체크 (RSI 유사 지표: 최근 5일 상승률)
    df["short_term_overheat"] = df.groupby("symbol")["close"].transform(
        lambda s: (s.pct_change(5) > 0.15).fillna(False).astype(int)
    )

    return df


# =========================
# Scoring
# =========================

def score_volume(latest: pd.DataFrame, cfg: SelectorConfig) -> pd.Series:
    z_turn = _z_norm(latest["turnover_krw"].fillna(0)).map(_sigmoid)
    z_spike = _z_norm(latest["vol_spike_ratio"]).map(_sigmoid)
    # 일중 변동성 사용 (시가 기준, 없으면 종가 기준 fallback)
    vola_col = latest.get("intraday_volatility", latest.get("hlc_volatility", pd.Series(0.0, index=latest.index)))
    z_vola = _z_norm(vola_col.fillna(0)).map(_sigmoid)

    score = (
        cfg.w_turnover * z_turn +
        cfg.w_vol_spike * z_spike +
        cfg.w_volatility * z_vola
    )

    if cfg.phase == "normal":
        ok = (
            (latest["vol_spike_ratio"] >= cfg.vol_spike_ratio_min) &
            (latest["hlc_volatility"] >= cfg.intraday_volatility_min)
        )
        return score.where(ok, 0.0)

    return score


def score_structure(latest: pd.DataFrame, cfg: SelectorConfig) -> pd.Series:
    """
    ============================================================
    [Secondary Filter] 구조형 점수 계산 (Structure Score)
    ============================================================
    
    목적: 구조형 종목의 정찰 가치를 0~100점으로 평가
    
    설계 기준 (구조 점수 체계):
    - 이동평균 구조: 35점 (MA 정배열 +20, 기울기 상승 +10, 밀집 후 확산 +5)
    - 그랜빌 법칙: 25점 (상향 돌파 +15, 지지 확인 +10, 이탈/이격 -5씩)
    - 고점·저점 구조: 25점 (Higher Low +10, 고점 갱신 +10, 박스 돌파 +5)
    - 안정성 보정: 15점 (변동성 적정 +5, 음봉 직후 아님 +5, 과열 아님 +5)
    
    중요 원칙:
    - 점수 단독 탈락 절대 금지 (우선순위 결정용)
    - 그랜빌 법칙은 보조 요소로만 사용 (탈락 기준으로 사용 금지)
    - 최종 점수 범위: 0 ~ 100점
    """
    scores = pd.Series(0.0, index=latest.index)
    
    # ============================================================
    # [구조 점수 구성 1] 이동평균 구조 (최대 35점)
    # ============================================================
    # 단/중/장기 MA 정배열: +20점
    ma_aligned = (
        (latest["ma5"] > latest["ma20"]) & 
        (latest["ma20"] > latest["ma60"])
    ).fillna(False)
    scores += ma_aligned.astype(int) * 20
    
    # MA 기울기 상승 전환: +10점
    ma_slope_up = (
        (latest["ma5_slope"] > 0) & 
        (latest["ma20_slope"] > 0)
    ).fillna(False)
    scores += ma_slope_up.astype(int) * 10
    
    # MA 밀집 후 확산: +5점
    ma_spread_reasonable = (
        (latest["ma_spread"] > 0.01) & 
        (latest["ma_spread"] < 0.05)
    ).fillna(False)
    scores += ma_spread_reasonable.astype(int) * 5
    
    # ============================================================
    # [구조 점수 구성 2] 그랜빌 법칙 (최대 25점, 보조 지표)
    # ============================================================
    # 중요: 그랜빌 법칙은 보조 요소로만 사용 (탈락 기준으로 사용 금지)
    
    # MA 상향 돌파: +15점
    ma_breakout = (
        (latest["close"] > latest["ma20"]) & 
        (latest["close"].shift(1) <= latest["ma20"].shift(1))
    ).fillna(False)
    scores += ma_breakout.astype(int) * 15
    
    # 눌림 후 MA 지지 확인: +10점
    ma_support = (
        (latest["low"] >= latest["ma20"] * 0.98) & 
        (latest["low"] <= latest["ma20"] * 1.02)
    ).fillna(False)
    scores += ma_support.astype(int) * 10
    
    # MA 이탈 경고: -5점 (보조 요소, 탈락 아님)
    ma_deviation = (
        (latest["close"] < latest["ma20"] * 0.95)
    ).fillna(False)
    scores -= ma_deviation.astype(int) * 5
    
    # MA 과도 이격: -5점 (보조 요소, 탈락 아님)
    ma_excessive_gap = (
        (latest["close"] > latest["ma20"] * 1.15)
    ).fillna(False)
    scores -= ma_excessive_gap.astype(int) * 5
    
    # ============================================================
    # [구조 점수 구성 3] 고점·저점 구조 (최대 25점)
    # ============================================================
    # Higher Low 형성: +10점
    higher_low = latest["higher_low"].fillna(0)
    scores += higher_low * 10
    
    # 최근 N일 고점 갱신: +10점
    new_high = latest["new_high"].fillna(0)
    scores += new_high * 10
    
    # 박스 상단 돌파 유지: +5점
    vola = latest["hlc_volatility"].fillna(0)
    box_breakout = (
        (vola >= cfg.struct_range_min) & 
        (vola <= cfg.struct_range_max) &
        ((latest["close"] - latest["low"]) / (latest["high"] - latest["low"]).replace(0, pd.NA) > 0.7)
    ).fillna(False)
    scores += box_breakout.astype(int) * 5
    
    # ============================================================
    # [구조 점수 구성 4] 안정성 보정 (최대 15점)
    # ============================================================
    # 변동성 과다 아님: +5점
    vola_reasonable = (
        (vola >= cfg.struct_range_min) & 
        (vola <= cfg.struct_range_max)
    ).fillna(False)
    scores += vola_reasonable.astype(int) * 5
    
    # 장대 음봉 직후 아님: +5점
    not_big_red = (latest["big_red_candle"] == 0).fillna(True)
    scores += not_big_red.astype(int) * 5
    
    # 단기 과열 상태 아님: +5점
    not_overheat = (latest["short_term_overheat"] == 0).fillna(True)
    scores += not_overheat.astype(int) * 5
    
    # ============================================================
    # [구조 점수] 최종 점수 범위 제한 (0 ~ 100점)
    # ============================================================
    # 중요: 점수 단독 탈락 절대 금지 (우선순위 결정용)
    scores = scores.clip(0, 100)
    
    return scores


def score_theme(latest: pd.DataFrame, theme_score: pd.Series, cfg: SelectorConfig) -> pd.Series:
    ts = theme_score.fillna(0).clip(0, 1)
    z_turn = _z_norm(latest["turnover_krw"].fillna(0)).map(_sigmoid)

    score = (cfg.w_theme * ts + cfg.w_theme_turnover * z_turn).clip(0, 1)

    if cfg.phase == "normal":
        return score.where(ts >= cfg.theme_min_score, 0.0)

    return score


# =========================
# Filters
# =========================

def apply_gate_filter(latest: pd.DataFrame, cfg: SelectorConfig) -> pd.DataFrame:
    """
    ============================================================
    [Gate Filter] 입구 필터
    ============================================================
    
    목적: 명백히 분석 대상이 될 수 없는 종목 제거 (판단 없음)
    
    설계 기준 (명시적 제외 조건):
    1. 거래량 = 0 제거
    2. 거래대금 < 25억 원 제거
    3. 관리종목 / 거래정지 / 상장폐지 예정 제거
    4. 필수 데이터 결손 존재 제거
    
    특징:
    - 판단 없이 명확한 기준으로만 제거
    - Gate Filter 통과 = 분석 가능한 종목 후보
    """
    filtered = latest.copy()
    
    # ============================================================
    # [Gate Filter 기준 1] 거래량 = 0 제거
    # ============================================================
    filtered = filtered[filtered["volume"] > 0]
    
    # ============================================================
    # [Gate Filter 기준 2] 거래대금 < 25억 원 제거
    # ============================================================
    filtered = filtered[filtered["turnover_krw"] >= cfg.gate_filter_min_turnover_krw]
    
    # ============================================================
    # [Gate Filter 기준 3] 최소 가격 필터 (관리/정지 종목 대체)
    # ============================================================
    # 관리종목/거래정지/상장폐지 예정 종목은 일반적으로 낮은 가격대에 분포
    # 최소 가격 필터로 일부 제거 (완벽하지 않지만 기본적인 필터링)
    filtered = filtered[filtered["close"] >= cfg.gate_filter_min_price]
    
    # TODO: 관리종목/거래정지/상장폐지 체크는 별도 데이터 소스 필요
    # 현재는 OHLCV 데이터만으로는 완벽한 판단 불가
    # 향후 외부 데이터 소스 연동 시 여기에 추가
    
    # ============================================================
    # [Gate Filter 기준 4] 필수 데이터 결손 존재 제거
    # ============================================================
    required_cols = ["open", "high", "low", "close", "volume", "turnover_krw"]
    filtered = filtered.dropna(subset=required_cols)
    
    return filtered


def apply_primary_filter(
    latest: pd.DataFrame,
    cfg: SelectorConfig,
    vol_spike_ratio: pd.Series,
    intraday_volatility: pd.Series,
) -> pd.DataFrame:
    """
    ============================================================
    [Primary Filter] 1차 필터
    ============================================================
    
    목적: 당일 실질적인 움직임이 발생한 종목을 넓게 포착 (Recall 우선)
    
    설계 기준 (OR 조건 - 하나 이상 만족 시 통과):
    1. 거래량 스파이크 >= 1.8
    2. 거래대금 >= 50억 원
    3. 일중 변동성 >= 3.0%
    
    특징:
    - OR 조건: 하나만 만족해도 통과 (넓은 포착)
    - Recall 우선: 놓치지 않는 것이 중요
    """
    # ============================================================
    # [Primary Filter 조건 1] 거래량 스파이크 >= 1.8
    # ============================================================
    condition1 = vol_spike_ratio >= cfg.primary_filter_vol_spike_min
    
    # ============================================================
    # [Primary Filter 조건 2] 거래대금 >= 50억 원
    # ============================================================
    condition2 = latest["turnover_krw"] >= cfg.primary_filter_min_turnover_krw
    
    # ============================================================
    # [Primary Filter 조건 3] 일중 변동성 >= 3.0%
    # ============================================================
    # 일중 변동성 = (고가 - 저가) ÷ 시가
    condition3 = intraday_volatility >= cfg.primary_filter_min_volatility
    
    # ============================================================
    # [Primary Filter] OR 조건 적용 (하나 이상 만족 시 통과)
    # ============================================================
    passed = condition1 | condition2 | condition3
    
    return latest[passed]


def manage_primary_filter_output_size(
    filtered: pd.DataFrame,
    cfg: SelectorConfig,
    original_latest: pd.DataFrame,
) -> pd.DataFrame:
    """
    1차 필터 출력 규모 관리
    
    목표:
    - 최소 30종목 보장
    - 권장 80종목
    - 최대 120종목
    - 120 초과 시 거래대금/거래량 스파이크 기준 점진적 상향
    """
    count = len(filtered)
    
    # 최소 30종목 미만이면 기준 완화 (단계적)
    if count < cfg.primary_filter_output_min:
        # 원본 데이터에서 기준 완화하여 재필터링
        vol_spike_ratio = original_latest["vol_spike_ratio"]
        intraday_volatility = original_latest["intraday_volatility"]
        
        # 기준을 10%씩 완화 (최대 3회)
        for step in range(1, 4):
            relaxed_vol_spike = cfg.primary_filter_vol_spike_min * (1.0 - 0.1 * step)
            relaxed_turnover = cfg.primary_filter_min_turnover_krw * (1.0 - 0.1 * step)
            relaxed_volatility = cfg.primary_filter_min_volatility * (1.0 - 0.1 * step)
            
            condition1 = vol_spike_ratio >= relaxed_vol_spike
            condition2 = original_latest["turnover_krw"] >= relaxed_turnover
            condition3 = intraday_volatility >= relaxed_volatility
            
            relaxed_filtered = original_latest[condition1 | condition2 | condition3]
            
            if len(relaxed_filtered) >= cfg.primary_filter_output_min:
                return relaxed_filtered
        
        # 여전히 부족하면 그대로 반환 (최소한의 필터링)
        return filtered
    
    # 최대 120종목 초과 시 기준 상향
    if count > cfg.primary_filter_output_max:
        vol_spike_ratio = filtered["vol_spike_ratio"]
        intraday_volatility = filtered["intraday_volatility"]
        
        # 기준을 10%씩 상향 (최대 3회)
        for step in range(1, 4):
            tightened_vol_spike = cfg.primary_filter_vol_spike_min * (1.0 + 0.1 * step)
            tightened_turnover = cfg.primary_filter_min_turnover_krw * (1.0 + 0.1 * step)
            tightened_volatility = cfg.primary_filter_min_volatility * (1.0 + 0.1 * step)
            
            condition1 = vol_spike_ratio >= tightened_vol_spike
            condition2 = filtered["turnover_krw"] >= tightened_turnover
            condition3 = intraday_volatility >= tightened_volatility
            
            tightened_filtered = filtered[condition1 | condition2 | condition3]
            
            if len(tightened_filtered) <= cfg.primary_filter_output_max:
                return tightened_filtered
        
        # 여전히 초과하면 거래대금 기준으로 상위 120개만 선택
        return filtered.nlargest(cfg.primary_filter_output_max, "turnover_krw")
    
    return filtered


# =========================
# Selection
# =========================

def select_watchlist(
    df: pd.DataFrame,
    *,
    cfg: SelectorConfig,
    largecap_symbols: List[str],
    theme_score_map: Optional[Dict[str, float]] = None,
) -> Dict[str, List[Dict]]:

    df_feat = compute_features(df, cfg)
    latest = df_feat.groupby("symbol", as_index=False).tail(1).set_index("symbol")

    # ============================================================
    # [단계 1] Gate Filter (입구 필터)
    # ============================================================
    # 목적: 명백히 분석 대상이 될 수 없는 종목 제거
    # 기준: 거래량=0, 거래대금<25억, 관리/정지 종목, 데이터 결손
    gate_filtered = apply_gate_filter(latest, cfg)
    
    # ============================================================
    # [단계 2] Primary Filter (1차 필터)
    # ============================================================
    # 목적: 당일 실질적인 움직임이 발생한 종목을 넓게 포착
    # 기준: OR 조건 (거래량 스파이크>=1.8 OR 거래대금>=50억 OR 변동성>=3.0%)
    vol_spike_ratio = gate_filtered["vol_spike_ratio"]
    intraday_volatility = gate_filtered["intraday_volatility"]
    
    primary_filtered = apply_primary_filter(
        gate_filtered,
        cfg,
        vol_spike_ratio,
        intraday_volatility,
    )
    
    # 출력 규모 관리 (최소 30, 권장 80, 최대 120종목)
    primary_filtered = manage_primary_filter_output_size(
        primary_filtered,
        cfg,
        gate_filtered,  # 원본 데이터 (Gate Filter 통과)
    )
    
    # ============================================================
    # [단계 3] Secondary Filter (2차 필터)
    # ============================================================
    # 목적: 정찰 가치가 있는 종목으로 압축 및 우선순위 결정
    # 버킷: volume (거래량형), structure (구조형), theme (테마형)
    # 구조형: 구조 점수(0~100점) 사용, 그랜빌 법칙은 보조 요소로만 사용
    universe = primary_filtered

    largecap = []
    for s in largecap_symbols:
        if s not in latest.index:
            continue
        row = latest.loc[s]
        close_price = float(row.get("close", 0))
        turnover = float(row.get("turnover_krw", 0))
        reason_summary = f"대형주 고정 선정 (종가: {close_price:,.0f}원, 거래대금: {turnover:,.0f}원)"
        
        largecap.append({
            "symbol": s,  # 종목코드
            "category": "largecap",  # 카테고리
            "bucket": "largecap",  # 호환성 유지
            "score": 1.0,
            "reason": {
                "summary": reason_summary,  # 선정 사유 요약
                "close": close_price,
                "turnover_krw": turnover,
            },
            "indicators": {  # 사용된 주요 지표 값
                "close": close_price,
                "turnover_krw": turnover,
            }
        })
    picked = {item["symbol"] for item in largecap}

    # ============================================================
    # [Secondary Filter] 버킷별 점수 계산
    # ============================================================
    # volume 버킷: 거래량형 점수 계산
    vol_scores = score_volume(universe, cfg)
    
    # structure 버킷: 구조형 점수 계산 (0~100점)
    # 중요: 구조 점수는 우선순위 결정용, 탈락 기준으로 사용 금지
    struct_scores = score_structure(universe, cfg)

    theme_score_map = theme_score_map or {}
    # theme_score_map이 {symbol: {score: float, sources: List[str]}} 형태일 수 있음
    theme_series = pd.Series({
        s: (
            theme_score_map[s]["score"] 
            if isinstance(theme_score_map.get(s), dict) and "score" in theme_score_map[s]
            else (theme_score_map.get(s) if isinstance(theme_score_map.get(s), (int, float)) else 0.0)
        )
        for s in universe.index
    })
    theme_scores = score_theme(universe, theme_series, cfg)

    def _pick_volume(scores: pd.Series, k: int):
        """거래량 기반 선정 (상세 이유 포함)"""
        out = []
        for sym, sc in scores.sort_values(ascending=False).items():
            if sym in picked or sc <= 0:
                continue
            
            row = universe.loc[sym]
            vol_spike = float(row.get("vol_spike_ratio", 0))
            turnover = float(row.get("turnover_krw", 0))
            volatility = float(row.get("hlc_volatility", 0))
            
            # 선정 사유 요약 생성
            reason_summary = (
                f"거래량형 선정 (거래대금: {turnover:,.0f}원, "
                f"거래량 스파이크: {vol_spike:.2f}배, "
                f"변동성: {volatility*100:.2f}%)"
            )
            
            out.append({
                "symbol": sym,  # 종목코드
                "category": "volume",  # 카테고리 (출력 메타 필드)
                "bucket": "volume",  # 호환성 유지
                "score": float(sc),
                "selection_reason": reason_summary,  # 선정 사유 요약 (출력 메타 필드)
                "reason": {
                    "summary": reason_summary,  # 선정 사유 요약 (호환성 유지)
                    "turnover_krw": turnover,
                    "vol_spike_ratio": vol_spike,
                    "hlc_volatility": volatility,
                },
                "indicators": {  # 사용된 주요 지표 값 (출력 메타 필드)
                    "turnover_krw": turnover,
                    "vol_spike_ratio": vol_spike,
                    "hlc_volatility": volatility,
                }
            })
            picked.add(sym)
            if len(out) >= k:
                break
        return out

    def _pick_structure(scores: pd.Series, k: int):
        """
        [Secondary Filter] 구조형 종목 선정
        
        구조 점수(Structure Score) 기반 선정:
        - 구조 점수 60점 이상 우선 선택
        - 구조형 후보군: Top 8 ~ 12
        - 구조 점수는 우선순위 결정용 (탈락 기준 아님)
        """
        out = []
        # 60점 이상 우선 정렬
        sorted_scores = scores.sort_values(ascending=False)
        
        # 60점 이상 종목 먼저 선택
        high_scores = sorted_scores[sorted_scores >= cfg.quota.structure_min_score]
        for sym, sc in high_scores.items():
            if sym in picked:
                continue
            
            row = universe.loc[sym]
            ma_aligned = bool(
                (row.get("ma5", 0) > row.get("ma20", 0)) and
                (row.get("ma20", 0) > row.get("ma60", 0))
            )
            ma_breakout = bool(
                (row.get("close", 0) > row.get("ma20", 0)) and
                (row.get("close", 0) <= row.get("ma20", 0) * 1.15)
            )
            higher_low = bool(row.get("higher_low", 0))
            new_high = bool(row.get("new_high", 0))
            
            # 선정 사유 요약 생성
            reason_parts = []
            if ma_aligned:
                reason_parts.append("MA 정배열")
            if ma_breakout:
                reason_parts.append("MA 상향 돌파")
            if higher_low:
                reason_parts.append("Higher Low")
            if new_high:
                reason_parts.append("고점 갱신")
            reason_summary = f"구조형 선정 (점수: {sc:.0f}점"
            if reason_parts:
                reason_summary += f", {', '.join(reason_parts)}"
            reason_summary += ")"
            
            out.append({
                "symbol": sym,  # 종목코드
                "category": "structure",  # 카테고리 (출력 메타 필드)
                "bucket": "structure",  # 호환성 유지
                "score": float(sc),
                "structure_score": float(sc),  # 구조 점수 (0~100점, 출력 메타 필드)
                "selection_reason": reason_summary,  # 선정 사유 요약 (출력 메타 필드)
                "reason": {
                    "summary": reason_summary,  # 선정 사유 요약 (호환성 유지)
                    "structure_score": float(sc),
                    "ma_aligned": ma_aligned,
                    "ma_breakout": ma_breakout,
                    "higher_low": higher_low,
                    "new_high": new_high,
                },
                "indicators": {  # 사용된 주요 지표 값 (출력 메타 필드)
                    "structure_score": float(sc),
                    "ma5": float(row.get("ma5", 0)),
                    "ma20": float(row.get("ma20", 0)),
                    "ma60": float(row.get("ma60", 0)),
                    "close": float(row.get("close", 0)),
                }
            })
            picked.add(sym)
            if len(out) >= cfg.quota.structure_candidate_max:
                break
        
        # 60점 미만이지만 상위 종목도 추가 (최소 8종목 보장)
        if len(out) < cfg.quota.structure_candidate_min:
            remaining = sorted_scores[sorted_scores < cfg.quota.structure_min_score]
            for sym, sc in remaining.items():
                if sym in picked:
                    continue
                
                row = universe.loc[sym]
                reason_summary = f"구조형 선정 (점수: {sc:.0f}점, 상위 종목)"
                
                out.append({
                    "symbol": sym,  # 종목코드
                    "category": "structure",  # 카테고리 (출력 메타 필드)
                    "bucket": "structure",  # 호환성 유지
                    "score": float(sc),
                    "structure_score": float(sc),  # 구조 점수 (0~100점, 출력 메타 필드)
                    "selection_reason": reason_summary,  # 선정 사유 요약 (출력 메타 필드)
                    "reason": {
                        "summary": reason_summary,  # 선정 사유 요약 (호환성 유지)
                        "structure_score": float(sc),
                        "ma_aligned": False,
                        "ma_breakout": False,
                        "higher_low": False,
                        "new_high": False,
                    },
                    "indicators": {  # 사용된 주요 지표 값 (출력 메타 필드)
                        "structure_score": float(sc),
                        "ma5": float(row.get("ma5", 0)),
                        "ma20": float(row.get("ma20", 0)),
                        "ma60": float(row.get("ma60", 0)),
                        "close": float(row.get("close", 0)),
                    }
                })
                picked.add(sym)
                if len(out) >= cfg.quota.structure_candidate_min:
                    break
        
        # 최종 선정 (k개만)
        return out[:k]

    def _pick_theme(scores: pd.Series, k: int):
        """테마 기반 선정 (상세 이유 포함)"""
        out = []
        for sym, sc in scores.sort_values(ascending=False).items():
            if sym in picked or sc <= 0:
                continue
            
            row = universe.loc[sym]
            theme_score = float(theme_series.get(sym, 0.0))
            turnover = float(row.get("turnover_krw", 0))
            
            # 출처 정보 추출
            theme_info = theme_score_map.get(sym, {})
            sources = []
            if isinstance(theme_info, dict) and "sources" in theme_info:
                sources = theme_info["sources"]
            elif isinstance(theme_info, (int, float)):
                # 기존 형식 (숫자만) - 출처 없음
                pass
            
            # 선정 사유 요약 생성
            sources_str = ", ".join(sources[:3]) if sources else "일반"
            reason_summary = (
                f"테마형 선정 (테마 점수: {theme_score:.2f}, "
                f"거래대금: {turnover:,.0f}원, 출처: {sources_str})"
            )
            
            reason = {
                "summary": reason_summary,  # 선정 사유 요약
                "theme_score": theme_score,
                "turnover_krw": turnover,
            }
            if sources:
                reason["sources"] = sources
            
            out.append({
                "symbol": sym,  # 종목코드
                "category": "theme",  # 카테고리 (출력 메타 필드)
                "bucket": "theme",  # 호환성 유지
                "score": float(sc),
                "selection_reason": reason_summary,  # 선정 사유 요약 (출력 메타 필드)
                "reason": reason,
                "indicators": {  # 사용된 주요 지표 값 (출력 메타 필드)
                    "theme_score": theme_score,
                    "turnover_krw": turnover,
                    "sources": sources,
                }
            })
            picked.add(sym)
            if len(out) >= k:
                break
        return out

    # 초기 선정
    volume_candidates = _pick_volume(vol_scores, cfg.quota.max_per_category)
    structure_candidates = _pick_structure(struct_scores, cfg.quota.max_per_category)
    theme_candidates = _pick_theme(theme_scores, cfg.quota.max_per_category)
    
    # 최종 후보군 압축 (5~6종목)
    final_result = _compress_final_candidates(
        largecap=largecap,
        volume_candidates=volume_candidates,
        structure_candidates=structure_candidates,
        theme_candidates=theme_candidates,
        cfg=cfg,
    )
    
    return final_result


def _compress_final_candidates(
    largecap: List[Dict],
    volume_candidates: List[Dict],
    structure_candidates: List[Dict],
    theme_candidates: List[Dict],
    cfg: SelectorConfig,
) -> Dict[str, List[Dict]]:
    """
    최종 후보군 압축
    
    목표:
    - 최종 정찰 대상 수: 5 ~ 6종목
    - 권장 구성: 거래량형 2, 구조형 2, 테마형 1~2
    - 단일 카테고리 3종목 초과 금지
    - 특정 카테고리 부족 시 타 카테고리에서 보충
    """
    result = {
        "largecap": largecap,
        "volume": [],
        "structure": [],
        "theme": [],
    }
    
    # 대형주는 항상 포함
    picked = {item["symbol"] for item in largecap}
    
    # 권장 구성: 거래량형 2, 구조형 2, 테마형 1~2
    target_volume = 2
    target_structure = 2
    target_theme_min = 1
    target_theme_max = 2
    
    # 거래량형 선정 (최대 2개)
    for item in volume_candidates:
        if item["symbol"] not in picked and len(result["volume"]) < target_volume:
            result["volume"].append(item)
            picked.add(item["symbol"])
    
    # 구조형 선정 (최대 2개, 60점 이상 우선)
    structure_sorted = sorted(
        structure_candidates,
        key=lambda x: x["score"],
        reverse=True
    )
    for item in structure_sorted:
        if item["symbol"] not in picked and len(result["structure"]) < target_structure:
            result["structure"].append(item)
            picked.add(item["symbol"])
    
    # 테마형 선정 (1~2개)
    theme_sorted = sorted(
        theme_candidates,
        key=lambda x: x["score"],
        reverse=True
    )
    for item in theme_sorted:
        if item["symbol"] not in picked and len(result["theme"]) < target_theme_max:
            result["theme"].append(item)
            picked.add(item["symbol"])
            if len(result["theme"]) >= target_theme_min:
                break
    
    # 총 개수 확인 및 보정
    total_count = (
        len(result["largecap"]) +
        len(result["volume"]) +
        len(result["structure"]) +
        len(result["theme"])
    )
    
    # 최소 개수 미달 시 보충
    if total_count < cfg.quota.final_target_min:
        # 부족한 개수만큼 보충
        needed = cfg.quota.final_target_min - total_count
        
        # 거래량형 부족 시 보충
        if len(result["volume"]) < target_volume:
            for item in volume_candidates:
                if item["symbol"] not in picked and len(result["volume"]) < target_volume:
                    result["volume"].append(item)
                    picked.add(item["symbol"])
                    needed -= 1
                    if needed <= 0:
                        break
        
        # 구조형 부족 시 보충
        if needed > 0 and len(result["structure"]) < target_structure:
            for item in structure_sorted:
                if item["symbol"] not in picked and len(result["structure"]) < target_structure:
                    result["structure"].append(item)
                    picked.add(item["symbol"])
                    needed -= 1
                    if needed <= 0:
                        break
        
        # 테마형 부족 시 보충
        if needed > 0 and len(result["theme"]) < target_theme_max:
            for item in theme_sorted:
                if item["symbol"] not in picked and len(result["theme"]) < target_theme_max:
                    result["theme"].append(item)
                    picked.add(item["symbol"])
                    needed -= 1
                    if needed <= 0:
                        break
    
    # 최대 개수 초과 시 압축
    total_count = (
        len(result["largecap"]) +
        len(result["volume"]) +
        len(result["structure"]) +
        len(result["theme"])
    )
    
    if total_count > cfg.quota.final_target_max:
        # 각 카테고리에서 낮은 점수부터 제거
        excess = total_count - cfg.quota.final_target_max
        
        # 테마형부터 제거 (우선순위 낮음)
        while excess > 0 and len(result["theme"]) > target_theme_min:
            result["theme"].pop()
            excess -= 1
        
        # 구조형 제거
        while excess > 0 and len(result["structure"]) > 1:
            result["structure"].pop()
            excess -= 1
        
        # 거래량형 제거
        while excess > 0 and len(result["volume"]) > 1:
            result["volume"].pop()
            excess -= 1
    
    # 단일 카테고리 3종목 초과 금지 확인
    if len(result["volume"]) > cfg.quota.max_per_category:
        result["volume"] = result["volume"][:cfg.quota.max_per_category]
    if len(result["structure"]) > cfg.quota.max_per_category:
        result["structure"] = result["structure"][:cfg.quota.max_per_category]
    if len(result["theme"]) > cfg.quota.max_per_category:
        result["theme"] = result["theme"][:cfg.quota.max_per_category]
    
    return result
