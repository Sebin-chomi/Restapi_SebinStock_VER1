# ===============================
# test/framework/analyzer/graph_generator.py
# ===============================
"""
Daily Report Graph Generator

정찰봇 일일 보고서 고정 그래프 세트 (v1)
"""
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("⚠️  matplotlib가 설치되지 않았습니다. 그래프 생성이 불가능합니다.")


# ===============================
# 그래프 스타일 설정
# ===============================
def setup_style():
    """그래프 스타일 설정"""
    if not HAS_MATPLOTLIB:
        return
    
    plt.style.use('default')
    plt.rcParams['font.family'] = 'Malgun Gothic'  # Windows 한글 폰트
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['figure.figsize'] = (10, 6)
    plt.rcParams['figure.dpi'] = 100


# ===============================
# 1. Cycle 종료 유형 분포 (Bar Chart)
# ===============================
def plot_cycle_outcomes(
    outcome_dist: Dict[str, int],
    output_path: str,
) -> bool:
    """
    Cycle 종료 유형 분포 (Bar Chart)
    
    "잘 됐다 / 못 됐다" 해석 ❌
    비율만 본다
    """
    if not HAS_MATPLOTLIB:
        return False
    
    try:
        setup_style()
        
        exit_types = ["reached_1pct", "no_reaction", "timeout", "manual_stop"]
        labels = {
            "reached_1pct": "1% 도달 종료",
            "no_reaction": "반응 실패 종료",
            "timeout": "타임아웃 종료",
            "manual_stop": "즉시 종료",
        }
        
        counts = [outcome_dist.get(et, 0) for et in exit_types]
        label_names = [labels[et] for et in exit_types]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        bars = ax.bar(label_names, counts, color=['#4CAF50', '#FF9800', '#2196F3', '#F44336'])
        
        # 값 표시
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2.,
                    height,
                    f'{int(height)}',
                    ha='center',
                    va='bottom'
                )
        
        ax.set_ylabel('Cycle 개수')
        ax.set_title('Cycle 종료 유형 분포', fontsize=14, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return True
    except Exception as e:
        print(f"⚠️  Cycle 종료 유형 분포 그래프 생성 오류: {e}")
        return False


# ===============================
# 2. 유지 시간 분포 (Histogram)
# ===============================
def plot_cycle_duration_hist(
    cycles: List[Dict[str, Any]],
    output_path: str,
) -> bool:
    """
    유지 시간 분포 (Histogram)
    
    평균은 거짓말을 할 수 있다
    분포는 거짓말을 못 한다
    """
    if not HAS_MATPLOTLIB:
        return False
    
    try:
        setup_style()
        
        durations = []
        for cycle in cycles:
            duration_sec = cycle.get("duration_sec", 0)
            if duration_sec > 0:
                # 초를 분으로 변환
                duration_min = duration_sec / 60
                durations.append(duration_min)
        
        if not durations:
            print("⚠️  유지 시간 데이터가 없습니다.")
            return False
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # 히스토그램 생성
        n, bins, patches = ax.hist(
            durations,
            bins=30,
            edgecolor='black',
            alpha=0.7,
            color='#2196F3'
        )
        
        # 평균선 표시
        mean_duration = np.mean(durations)
        ax.axvline(
            mean_duration,
            color='red',
            linestyle='--',
            linewidth=2,
            label=f'평균: {mean_duration:.1f}분'
        )
        
        ax.set_xlabel('Cycle 유지 시간 (분)')
        ax.set_ylabel('Cycle 개수')
        ax.set_title('Cycle 유지 시간 분포', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return True
    except Exception as e:
        print(f"⚠️  유지 시간 분포 그래프 생성 오류: {e}")
        return False


# ===============================
# 3. 종료 가격대 분포 (Price Zone Histogram)
# ===============================
def plot_price_zone_hist(
    cycles: List[Dict[str, Any]],
    output_path: str,
) -> bool:
    """
    종료 가격대 분포 (Price Zone Histogram)
    
    지지·저항 후보를 사후적으로 드러내는 유일한 시각화
    
    선 긋기 ❌
    "여기가 지지"라고 말하지 않는다
    → "여기서 많이 끝났다"까지만
    """
    if not HAS_MATPLOTLIB:
        return False
    
    try:
        setup_style()
        
        # 종료 가격 수집 (snapshot에서 가져와야 함)
        # 현재는 cycle에 가격 정보가 없으므로, 추후 구현 필요
        # 일단 구조만 제공
        
        print("⚠️  종료 가격대 분포 그래프는 가격 데이터가 필요합니다.")
        print("    현재 cycle 데이터에 가격 정보가 없어 생성하지 않습니다.")
        
        # TODO: cycle에 종료 시점 가격 정보 추가 후 구현
        return False
    except Exception as e:
        print(f"⚠️  종료 가격대 분포 그래프 생성 오류: {e}")
        return False


# ===============================
# 4. 장중 시간대별 Cycle 발생 수 (Time-of-Day Line Chart)
# ===============================
def plot_time_of_day_cycles(
    cycles: List[Dict[str, Any]],
    output_path: str,
) -> bool:
    """
    장중 시간대별 Cycle 발생 수 (Time-of-Day Line Chart)
    
    정찰봇이 언제 가장 예민하게 반응하는지 확인 가능
    장 초반 / 중반 / 후반의 구조 차이를 감으로 느끼게 해줌
    """
    if not HAS_MATPLOTLIB:
        return False
    
    try:
        setup_style()
        
        # 시간대별 cycle 시작 수 집계 (10분 단위)
        time_bins = {}
        
        for cycle in cycles:
            start_time_str = cycle.get("start_time", "")
            if not start_time_str:
                continue
            
            try:
                start_dt = datetime.fromisoformat(
                    start_time_str.replace("Z", "+00:00")
                )
                # 시간을 10분 단위로 반올림
                hour = start_dt.hour
                minute = (start_dt.minute // 10) * 10
                time_key = f"{hour:02d}:{minute:02d}"
                
                time_bins[time_key] = time_bins.get(time_key, 0) + 1
            except Exception:
                continue
        
        if not time_bins:
            print("⚠️  시간대별 cycle 데이터가 없습니다.")
            return False
        
        # 시간순 정렬
        sorted_times = sorted(time_bins.keys())
        counts = [time_bins[t] for t in sorted_times]
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.plot(sorted_times, counts, marker='o', linewidth=2, markersize=6, color='#2196F3')
        ax.fill_between(sorted_times, counts, alpha=0.3, color='#2196F3')
        
        ax.set_xlabel('시간대 (10분 단위)')
        ax.set_ylabel('Cycle 발생 수')
        ax.set_title('장중 시간대별 Cycle 발생 수', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # x축 레이블 회전
        plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return True
    except Exception as e:
        print(f"⚠️  시간대별 Cycle 발생 수 그래프 생성 오류: {e}")
        return False


# ===============================
# 메인 그래프 생성 함수
# ===============================
def generate_daily_graphs(
    daily_report_path: str,
    output_dir: str,
) -> Dict[str, bool]:
    """
    Daily Report에서 그래프 생성
    
    Args:
        daily_report_path: daily_report.json 파일 경로
        output_dir: 그래프 저장 디렉토리
    
    Returns:
        생성된 그래프 파일 경로 딕셔너리
    """
    if not HAS_MATPLOTLIB:
        print("⚠️  matplotlib가 설치되지 않아 그래프를 생성할 수 없습니다.")
        return {}
    
    # daily_report.json 읽기
    try:
        with open(daily_report_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)
    except Exception as e:
        print(f"⚠️  Daily Report 읽기 오류: {e}")
        return {}
    
    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)
    
    results = {}
    
    # 1. Cycle 종료 유형 분포
    outcome_dist = report_data.get("cycle_outcome_distribution", {})
    if outcome_dist:
        output_path = os.path.join(output_dir, "cycle_outcomes.png")
        results["cycle_outcomes"] = plot_cycle_outcomes(
            outcome_dist,
            output_path
        )
        if results["cycle_outcomes"]:
            print(f"  ✅ 생성: {output_path}")
    
    # 2. 유지 시간 분포
    cycles = report_data.get("representative_cycles", [])
    # 모든 cycle 데이터가 필요하므로 daily_analysis.json에서 가져와야 함
    # 일단 representative_cycles만 사용
    
    # 전체 cycle 데이터를 위해 daily_analysis.json도 읽기
    daily_analysis_path = daily_report_path.replace(
        "daily_report.json", "daily_analysis.json"
    )
    all_cycles = []
    
    if os.path.exists(daily_analysis_path):
        try:
            with open(daily_analysis_path, "r", encoding="utf-8") as f:
                analysis_data = json.load(f)
            observer_stats = analysis_data.get("observer_stats", {})
            observer_summary = observer_stats.get("observer_summary", {})
            cycle_summary_list = observer_summary.get("cycle_summary", [])
            all_cycles = cycle_summary_list
        except Exception:
            pass
    
    if all_cycles:
        output_path = os.path.join(output_dir, "cycle_duration_hist.png")
        results["cycle_duration_hist"] = plot_cycle_duration_hist(
            all_cycles,
            output_path
        )
        if results.get("cycle_duration_hist"):
            print(f"  ✅ 생성: {output_path}")
    
    # 3. 종료 가격대 분포 (현재는 구현 안 됨)
    # output_path = os.path.join(output_dir, "price_zone_hist.png")
    # results["price_zone_hist"] = plot_price_zone_hist(all_cycles, output_path)
    
    # 4. 장중 시간대별 Cycle 발생 수
    if all_cycles:
        output_path = os.path.join(output_dir, "time_of_day_cycles.png")
        results["time_of_day_cycles"] = plot_time_of_day_cycles(
            all_cycles,
            output_path
        )
        if results.get("time_of_day_cycles"):
            print(f"  ✅ 생성: {output_path}")
    
    return results











