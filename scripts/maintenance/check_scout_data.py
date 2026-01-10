#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""오늘 수집된 정찰 데이터 검토 스크립트"""
import json
import sys
from pathlib import Path
from collections import defaultdict

# 프로젝트 루트로 이동
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
sys.path.insert(0, str(project_root))

file_path = project_root / "records/scout/2026-01-07/000660.jsonl"

if not file_path.exists():
    print(f"[ERROR] 파일이 없습니다: {file_path}")
    exit(1)

# 데이터 로드
data = []
with open(file_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            data.append(json.loads(line))
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON 파싱 오류: {e}")

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 60)
print("정찰 데이터 검토 결과 - 2026-01-07 (000660)")
print("=" * 60)

# 기본 통계
print(f"\n[OK] 총 레코드 수: {len(data)}")
if data:
    print(f"[TIME] 시간 범위: {data[0]['meta']['time']} ~ {data[-1]['meta']['time']}")
    
    # Session 분포
    sessions = defaultdict(int)
    for r in data:
        sessions[r['meta']['session']] += 1
    print(f"\n[SESSION] Session 분포:")
    for session, count in sorted(sessions.items()):
        print(f"   - {session}: {count}개")
    
    # Interval 분포
    intervals = defaultdict(int)
    for r in data:
        intervals[r['interval_min']] += 1
    print(f"\n[INTERVAL] Interval 분포:")
    for interval, count in sorted(intervals.items()):
        print(f"   - {interval}분: {count}개")
    
    # Observer 통계
    triggered_count = sum(1 for r in data if r['observer']['triggered'])
    buy_signal_count = sum(1 for r in data if r['observer'].get('buy_signal'))
    sell_signal_count = sum(1 for r in data if r['observer'].get('sell_signal'))
    
    print(f"\n[OBSERVER] Observer 통계:")
    print(f"   - Triggered: {triggered_count}/{len(data)} ({triggered_count*100/len(data):.1f}%)")
    print(f"   - Buy Signal: {buy_signal_count}/{len(data)} ({buy_signal_count*100/len(data):.1f}%)")
    print(f"   - Sell Signal: {sell_signal_count}/{len(data)} ({sell_signal_count*100/len(data):.1f}%)")
    
    # Snapshot 통계
    price_checked_count = sum(1 for r in data if r['snapshot']['price_checked'])
    high_updated_count = sum(1 for r in data if r['snapshot'].get('high_updated'))
    low_updated_count = sum(1 for r in data if r['snapshot'].get('low_updated'))
    
    print(f"\n[SNAPSHOT] Snapshot 통계:")
    print(f"   - 가격 조회 성공: {price_checked_count}/{len(data)} ({price_checked_count*100/len(data):.1f}%)")
    print(f"   - 고가 갱신: {high_updated_count}회")
    print(f"   - 저가 갱신: {low_updated_count}회")
    
    if price_checked_count > 0:
        prices = [r['snapshot']['current_price'] for r in data if r['snapshot'].get('current_price')]
        if prices:
            print(f"   - 가격 범위: {min(prices):,}원 ~ {max(prices):,}원")
    
    # Base Candle 통계
    base_candle_exists_count = sum(1 for r in data if r['base_candle'].get('exists'))
    print(f"\n[BASE_CANDLE] Base Candle 통계:")
    print(f"   - 존재: {base_candle_exists_count}/{len(data)} ({base_candle_exists_count*100/len(data):.1f}%)")
    
    # Box 통계
    box_formed_count = sum(1 for r in data if r['box'].get('formed'))
    print(f"\n[BOX] Box 통계:")
    print(f"   - 형성: {box_formed_count}/{len(data)} ({box_formed_count*100/len(data):.1f}%)")
    
    # Meta 정보 확인
    first_valid_date_count = sum(1 for r in data if r['meta'].get('first_valid_date') == '2026-01-07')
    print(f"\n[META] Meta 정보:")
    print(f"   - first_valid_date 설정: {first_valid_date_count}/{len(data)} ({first_valid_date_count*100/len(data):.1f}%)")
    
    # 데이터 품질 검사
    print(f"\n[QUALITY] 데이터 품질 검사:")
    issues = []
    
    # 시간 간격 검사
    if len(data) > 1:
        time_gaps = []
        for i in range(1, len(data)):
            prev_time = data[i-1]['meta']['time']
            curr_time = data[i]['meta']['time']
            # 간단한 시간 차이 계산 (HH:MM:SS 형식)
            prev_parts = prev_time.split(':')
            curr_parts = curr_time.split(':')
            prev_min = int(prev_parts[0]) * 60 + int(prev_parts[1])
            curr_min = int(curr_parts[0]) * 60 + int(curr_parts[1])
            gap = curr_min - prev_min
            if gap < 0:
                gap += 24 * 60  # 다음날 처리
            time_gaps.append(gap)
        
        expected_intervals = [r['interval_min'] for r in data[1:]]
        mismatches = sum(1 for gap, expected in zip(time_gaps, expected_intervals) if gap != expected)
        if mismatches > 0:
            issues.append(f"[WARN] 시간 간격 불일치: {mismatches}개")
        else:
            print("   [OK] 시간 간격 정상")
    
    # 모든 레코드에 first_valid_date가 있는지 확인
    if first_valid_date_count != len(data):
        issues.append(f"[WARN] first_valid_date 누락: {len(data) - first_valid_date_count}개")
    else:
        print("   [OK] first_valid_date 모두 설정됨")
    
    # 모든 레코드에 가격 정보가 있는지 확인
    if price_checked_count != len(data):
        issues.append(f"[WARN] 가격 조회 실패: {len(data) - price_checked_count}개")
    else:
        print("   [OK] 가격 정보 모두 수집됨")
    
    if issues:
        print("\n[ISSUES] 발견된 이슈:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("\n[OK] 데이터 품질 양호")
    
    print("\n" + "=" * 60)







