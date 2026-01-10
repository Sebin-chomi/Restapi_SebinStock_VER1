# ===============================
# test/scout_bot/config/loaders.py
# 설정 파일 로더
# ===============================
"""
설정 파일 로더

역할:
- YAML 설정 파일 로드
- 로드 실패 시 기본값 반환
"""
from __future__ import annotations

import yaml
from pathlib import Path
from typing import Dict, Any


# =========================
# 기본값 (Fallback)
# =========================

DEFAULT_THRESHOLDS = {
    "version": 1,
    "cooldown": {
        "minutes": 10,
    },
    "volume": {
        "spike": {
            "enabled": True,
            "window_minutes": 10,
            "ratio_min": 2.0,
        },
    },
    "turnover": {
        "threshold": {
            "enabled": True,
            "krw_min": 10_000_000_000,  # 100억
        },
    },
    "price": {
        "jump_drop": {
            "enabled": True,
            "pct_min": 3.0,
            "base_price": "prev_close",  # prev_close | day_open
        },
    },
    "day_range": {
        "high_break": {
            "enabled": True,
        },
        "low_break": {
            "enabled": True,
        },
    },
}


# =========================
# 설정 파일 경로
# =========================

def get_config_file_path() -> Path:
    """
    설정 파일 경로 반환
    
    Returns:
        설정 파일 경로
    """
    current_file = Path(__file__).resolve()
    # test/scout_bot/config/loaders.py → 프로젝트 루트
    project_root = current_file.parents[3]
    config_dir = project_root / "scout_bot" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    
    return config_dir / "event_thresholds.yaml"


# =========================
# 설정 로드
# =========================

def load_event_thresholds() -> Dict[str, Any]:
    """
    이벤트 임계값 설정 로드
    
    Returns:
        설정 딕셔너리 (로드 실패 시 기본값)
    """
    config_path = get_config_file_path()
    
    # 파일 없으면 기본값 반환
    if not config_path.exists():
        print(f"[SCOUT][WARN] event_thresholds.yaml not found, using defaults")
        return DEFAULT_THRESHOLDS.copy()
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        # None이면 기본값 반환
        if config is None:
            print(f"[SCOUT][WARN] event_thresholds.yaml is empty, using defaults")
            return DEFAULT_THRESHOLDS.copy()
        
        # 기본값과 병합 (누락된 키는 기본값 사용)
        merged = _merge_config(DEFAULT_THRESHOLDS.copy(), config)
        return merged
        
    except yaml.YAMLError as e:
        print(f"[SCOUT][WARN] event_thresholds.yaml parse error: {e}, using defaults")
        return DEFAULT_THRESHOLDS.copy()
    except Exception as e:
        print(f"[SCOUT][WARN] event_thresholds.yaml load error: {e}, using defaults")
        return DEFAULT_THRESHOLDS.copy()


def _merge_config(default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
    """
    기본값과 사용자 설정 병합 (재귀)
    
    Args:
        default: 기본값 딕셔너리
        user: 사용자 설정 딕셔너리
        
    Returns:
        병합된 딕셔너리
    """
    result = default.copy()
    
    for key, value in user.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # 재귀 병합
            result[key] = _merge_config(result[key], value)
        else:
            # 덮어쓰기
            result[key] = value
    
    return result






