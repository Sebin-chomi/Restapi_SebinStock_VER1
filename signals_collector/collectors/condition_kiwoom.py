# ===============================
# signals_collector/collectors/condition_kiwoom.py
# ===============================
"""
키움 조건검색식 수집기

장 마감 후 조건식별 종목 리스트를 수집하여
scout_selector/input/conditions/conditions_YYYYMMDD.json 생성
"""
import sys
from pathlib import Path
from typing import List, Dict, Optional, Callable
import json
from datetime import datetime

# 프로젝트 루트를 경로에 추가
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import requests
except ImportError:
    requests = None
    print("⚠️  requests 모듈이 없습니다. pip install requests")


# ===============================
# 설정 주입 (테스트/실전 분리)
# ===============================

def _get_config_from_test_module():
    """
    test 모듈에서 설정을 가져오기 (선택적)
    
    Returns:
        (get_token_func, host_url, app_key, app_secret) 또는 None
    """
    try:
        # test 모듈 import 시도 (여러 경로 시도)
        try:
            from test.login import fn_au10001 as get_token
            from test.config_test import host_url, app_key, app_secret
            return get_token, host_url, app_key, app_secret
        except ImportError:
            try:
                from test.login import fn_au10001 as get_token
                from test.config import host_url, app_key, app_secret
                return get_token, host_url, app_key, app_secret
            except ImportError:
                return None
    except Exception:
        return None


# ===============================
# 키움 API 호출
# ===============================

def get_condition_list(token: str, host_url: str, app_key: str, app_secret: str) -> List[Dict]:
    """
    조건식 목록 조회
    
    Args:
        token: 인증 토큰
        host_url: API 호스트 URL
        app_key: 앱 키
        app_secret: 앱 시크릿
    
    Returns:
        조건식 목록 [{"condition_id": "...", "condition_name": "...", ...}, ...]
    """
    if not requests:
        return []
    
    url = f"{host_url}/uapi/domestic-stock/v1/conditions"
    headers = {
        "authorization": f"Bearer {token}",
        "appkey": app_key,
        "appsecret": app_secret,
        "tr_id": "HHKST01000300",
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        return res.json().get("output", [])
    except Exception as e:
        print(f"⚠️  조건식 목록 조회 실패: {e}")
        return []


def run_condition(token: str, condition_id: str, host_url: str, app_key: str, app_secret: str) -> List[str]:
    """
    조건식 실행하여 종목 리스트 반환
    
    Args:
        token: 인증 토큰
        condition_id: 조건식 ID
        host_url: API 호스트 URL
        app_key: 앱 키
        app_secret: 앱 시크릿
    
    Returns:
        종목 코드 리스트 ["005930", "000660", ...]
    """
    if not requests:
        return []
    
    url = f"{host_url}/uapi/domestic-stock/v1/conditions/search"
    headers = {
        "authorization": f"Bearer {token}",
        "appkey": app_key,
        "appsecret": app_secret,
        "tr_id": "HHKST01000400",
    }
    
    try:
        res = requests.get(
            url,
            headers=headers,
            params={"condition_id": condition_id},
            timeout=10,
        )
        res.raise_for_status()
        return [x["stk_cd"] for x in res.json().get("output", [])]
    except Exception as e:
        print(f"⚠️  조건식 실행 실패 (condition_id={condition_id}): {e}")
        return []


# ===============================
# 수집 및 저장
# ===============================

def collect_conditions(
    output_dir: Path,
    date: str,
    condition_names: Optional[List[str]] = None,
    get_token_func: Optional[Callable] = None,
    host_url: Optional[str] = None,
    app_key: Optional[str] = None,
    app_secret: Optional[str] = None,
) -> bool:
    """
    조건식 수집 및 JSON 저장
    
    Args:
        output_dir: scout_selector/input/conditions/ 디렉토리
        date: 날짜 (YYYYMMDD)
        condition_names: 수집할 조건식 이름 리스트 (None이면 모든 조건식)
        get_token_func: 토큰 획득 함수 (None이면 test 모듈에서 자동 탐색)
        host_url: API 호스트 URL (None이면 test 모듈에서 자동 탐색)
        app_key: 앱 키 (None이면 test 모듈에서 자동 탐색)
        app_secret: 앱 시크릿 (None이면 test 모듈에서 자동 탐색)
    
    Returns:
        성공 여부
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"conditions_{date}.json"
    
    # 설정 가져오기 (주입받지 않았으면 test 모듈에서 자동 탐색)
    if get_token_func is None or host_url is None or app_key is None or app_secret is None:
        config = _get_config_from_test_module()
        if config:
            get_token_func, host_url, app_key, app_secret = config
        else:
            print("⚠️  키움 API 설정을 찾을 수 없습니다 (MOCK 모드)")
            # 빈 JSON 생성 (파이프라인 안전장치)
            empty_data = {
                "date": date,
                "source": "kiwoom_condition",
                "conditions": []
            }
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(empty_data, f, ensure_ascii=False, indent=2)
            print(f"📋 빈 조건식 파일 생성: {output_file}")
            return False
    
    # 토큰 획득
    try:
        token = get_token_func()
    except Exception as e:
        print(f"⚠️  토큰 획득 실패: {e}")
        # 빈 JSON 생성 (파이프라인 안전장치)
        empty_data = {
            "date": date,
            "source": "kiwoom_condition",
            "conditions": []
        }
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(empty_data, f, ensure_ascii=False, indent=2)
        print(f"📋 빈 조건식 파일 생성: {output_file}")
        return False
    
    # 조건식 목록 조회
    condition_list = get_condition_list(token, host_url, app_key, app_secret)
    if not condition_list:
        print("⚠️  조건식 목록이 비어있습니다")
        # 빈 JSON 생성 (파이프라인 안전장치)
        empty_data = {
            "date": date,
            "source": "kiwoom_condition",
            "conditions": []
        }
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(empty_data, f, ensure_ascii=False, indent=2)
        print(f"📋 빈 조건식 파일 생성: {output_file}")
        return False
    
    # 수집할 조건식 필터링
    if condition_names:
        filtered_conditions = [
            c for c in condition_list
            if c.get("condition_name") in condition_names
        ]
    else:
        # 모든 조건식 수집
        filtered_conditions = condition_list
    
    # 조건식별 종목 수집
    collected_conditions = []
    for cond in filtered_conditions:
        condition_id = cond.get("condition_id")
        condition_name = cond.get("condition_name", "unknown")
        
        if not condition_id:
            continue
        
        print(f"📋 조건식 수집 중: {condition_name} ({condition_id})")
        symbols = run_condition(token, condition_id, host_url, app_key, app_secret)
        
        if symbols:
            collected_conditions.append({
                "condition_name": condition_name,
                "symbols": symbols
            })
            print(f"   → {len(symbols)} 종목 수집")
        else:
            print(f"   → 종목 없음")
    
    # JSON 저장
    output_data = {
        "date": date,
        "source": "kiwoom_condition",
        "conditions": collected_conditions
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 조건식 수집 완료: {output_file}")
    print(f"   총 {len(collected_conditions)}개 조건식, {sum(len(c['symbols']) for c in collected_conditions)} 종목")
    
    return True
