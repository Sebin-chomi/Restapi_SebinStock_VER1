# Daily Report Schema (v1)

## 📋 개요

이 스키마는 **데이터 저장용이 아니라 "계약(contract)"**이다.

보고서 생성기, 그래프 생성기, 전략 분석기, 딥러닝 전처리 등  
👉 **모두가 이 스키마를 신뢰하게 만드는 게 목적**

---

## 🏗️ 전체 구조

```python
DailyReport
├── meta: ReportMeta                    # [A] 보고서 정체성
├── observer_stats: ObserverStats      # [B] Observer 실행 통계 (record 기준)
├── cycle_summary: CycleSummary        # [C] Cycle 요약 통계
├── cycle_outcome_distribution: CycleOutcomeDistribution  # [D] Cycle 결과 분포
├── representative_cycles: List[RepresentativeCycle]       # [E] 대표 Cycle (최대 2개)
├── observation_hints: ObservationHints                   # [F] 반복 관측 힌트
├── price_zone_summary: PriceZoneSummary                  # [G] 가격 구간 통계
└── manual_notes: ManualNotes                             # [H] 사람 입력 영역
```

---

## [A] ReportMeta - 보고서 정체성

**절대 해석 없음**  
**"이 보고서는 어떤 맥락에서 만들어졌는가"**

```python
@dataclass
class ReportMeta:
    date: str                    # YYYY-MM-DD
    generated_at: datetime       # 보고서 생성 시각
    scout_version: str           # 정찰봇 버전 (예: "scout_v1")
    test_mode: bool              # 테스트 여부
    condition_id: Optional[str]  # 조건식 ID (없을 수 있음)
```

### 예시
```json
{
  "date": "2026-01-05",
  "generated_at": "2026-01-05T20:13:01.187349",
  "scout_version": "scout_v1",
  "test_mode": true,
  "condition_id": null
}
```

---

## [B] ObserverStats - Observer 실행 통계 (record 기준)

**record = 사실의 최소 단위**  
**cycle과 의도적으로 분리**

```python
@dataclass
class ObserverStockStats:
    records: int                         # observer 실행 횟수
    observer_triggered_records: int     # triggered=True record 수

@dataclass
class ObserverStats:
    total_records: int
    total_stocks: int
    by_stock: Dict[str, ObserverStockStats]
```

### 예시
```json
{
  "total_records": 584,
  "total_stocks": 8,
  "by_stock": {
    "005930": {
      "records": 73,
      "observer_triggered_records": 73
    },
    "000660": {
      "records": 73,
      "observer_triggered_records": 73
    }
  }
}
```

---

## [C] CycleSummary - Cycle 요약 통계 (핵심)

**여기서부터 사건 단위**  
**triggered_cycles의 의미가 명확해짐**

```python
@dataclass
class CycleSummary:
    triggered_records: int      # record 단위 triggered 수
    triggered_cycles: int       # 종료된 cycle 수
    open_cycles: int            # 미종료 cycle 수
```

### 예시
```json
{
  "triggered_records": 584,
  "triggered_cycles": 8,
  "open_cycles": 8
}
```

### 용어 설명
- **triggered_records**: `observer.triggered == True`인 record 개수
- **triggered_cycles**: 완전히 종료된 cycle 개수 (exit_type 존재)
- **open_cycles**: 장 종료 시점에 미종료된 cycle 개수

---

## [D] CycleOutcomeDistribution - Cycle 결과 분포

**"좋다/나쁘다" 없음**  
**종료 이유의 분포만 기록**

```python
@dataclass
class CycleOutcomeDistribution:
    reached_1pct: int = 0    # 기준 반응 폭 도달
    no_reaction: int = 0     # 관측 시간 동안 의미 있는 반응 없음
    timeout: int = 0         # 최대 관측 시간 초과
    manual_stop: int = 0     # 시스템/테스트 종료
```

### 예시
```json
{
  "reached_1pct": 0,
  "no_reaction": 0,
  "timeout": 8,
  "manual_stop": 0
}
```

### exit_type 판정 기준

#### 대원칙
1. **exit_type은 반드시 하나만**
2. **숫자보다 이벤트 기준**
3. **성과/성공/실패 용어 금지**
   - "잘 됐냐?" ❌
   - "어떤 이유로 관측이 끝났냐?" ✅

#### v1 허용 exit_type (고정)
- `reached_1pct`: 기준 반응 폭 도달
- `no_reaction`: 관측 시간 동안 의미 있는 반응 없음
- `timeout`: 최대 관측 시간 초과
- `manual_stop`: 시스템/테스트 종료

**❗ 이 4개 외에는 v1에 넣지 않는다**

#### 우선순위 (같은 record에서 여러 조건 만족 시)
1. `manual_stop` (최우선: 사람이 멈추면 그게 최우선)
2. `reached_1pct` (반응 도달은 가장 명확한 종료)
3. `timeout` (timeout은 시스템 조건)
4. `no_reaction` (no_reaction은 "나머지")

---

## [E] RepresentativeCycle - 대표 Cycle 요약 (최대 2개)

**가격 ❌**  
**수익 ❌**  
**구조 재현용**

```python
@dataclass
class RepresentativeCycle:
    cycle_id: str              # 예: "2026-01-05-005930-01"
    stock: str                 # 종목 코드
    start_time: datetime       # cycle 시작 시각
    end_time: datetime         # cycle 종료 시각
    duration_sec: int          # 지속 시간 (초)
    exit_type: str             # 종료 사유
```

### 예시
```json
{
  "cycle_id": "2026-01-05-005930-01",
  "stock": "005930",
  "start_time": "2026-01-05T09:00:08.720909",
  "end_time": "2026-01-05T15:29:09.742795",
  "duration_sec": 23341,
  "exit_type": "timeout"
}
```

---

## [F] ObservationHints - 반복 관측 힌트 (통계 요약만)

**"왜 그런지" ❌**  
**"그랬다" ✅**

```python
@dataclass
class ObservationHints:
    dominant_exit_type: Optional[str] = None
    avg_cycle_duration_sec: Optional[float] = None
```

### 예시
```json
{
  "dominant_exit_type": "timeout",
  "avg_cycle_duration_sec": 23317.42
}
```

---

## [G] PriceZoneSummary - 가격 구간 통계 (지지·저항 후보)

**선 긋기 ❌**  
**후보 데이터만**

```python
@dataclass
class PriceZoneStat:
    price_zone: str            # 예: "72000-72500"
    exit_count: int
    no_reaction_count: int

@dataclass
class PriceZoneSummary:
    zones: List[PriceZoneStat]
```

### 예시
```json
{
  "zones": [
    {
      "price_zone": "72000-72500",
      "exit_count": 3,
      "no_reaction_count": 2
    }
  ]
}
```

**현재 v1에서는 빈 배열로 제공 (추후 구현)**

---

## [H] ManualNotes - 사람 입력 영역 (완전 분리)

**자동 생성 ❌**  
**수정 가능**  
**의미/해석 전용 공간**

```python
@dataclass
class ManualNotes:
    market_one_liner: Optional[str] = None
    confusing_cycle_id: Optional[str] = None
    unnecessary_action_note: Optional[str] = None
    free_memo: Optional[str] = None
```

### 예시
```json
{
  "market_one_liner": null,
  "confusing_cycle_id": null,
  "unnecessary_action_note": null,
  "free_memo": null
}
```

---

## 📊 Cycle 판정 로직

### Cycle 정의

**"observer가 어떤 조건을 포착한 이후, 그 반응을 관찰하다가 하나의 이유로 종료된 관측 묶음"**

- **시작**: 의미 있는 트리거 (`observer.triggered == True`)
- **끝**: 명시적인 종료 사유 (`outcome.exit_type` 존재)
- **중간**: 관찰 상태

### Cycle 상태 머신

각 종목은 항상 아래 중 하나의 상태:

- **IDLE**: cycle 없음
- **ACTIVE**: cycle 진행 중

**종목별로 동시에 ACTIVE cycle은 1개만 허용**

### Cycle 시작 조건

다음 중 하나라도 만족하면 시작:

- `observer.triggered == True`
- 이전 cycle이 종료된 이후 첫 triggered

**조건**:
- 같은 종목
- 이전 cycle이 열려 있지 않을 것

### Cycle 종료 조건

`outcome.exit_type`이 존재하고, v1 허용 exit_type 중 하나:

- `reached_1pct`
- `no_reaction`
- `timeout`
- `manual_stop`

**종료는 "조건"이 아니라 "이벤트"다**

한 record에서 exit 조건 충족 → 그 record를 `cycle_end_record`로 지정

### 장 종료 시 처리

모든 record를 처리한 뒤, 미종료 cycle을 `timeout`으로 종료 처리:

```python
for stock_code, cycle in open_cycles.items():
    cycle["exit_type"] = "timeout"
    cycle["end_reason"] = "session_end"
    # triggered_cycle에 추가
```

### triggered_cycles 집계 기준

**triggered_cycles = 오늘 "완전히 종료된" cycle의 개수**

**포함 ❌**:
- 아직 열려 있는 cycle
- 장 종료 시점에 진행 중인 관측

**이유**: 종료되지 않은 건 아직 하나의 사건이 아님

---

## 📁 파일 위치

- **스키마 정의**: `test/framework/analyzer/daily_report_schema.py`
- **빌더**: `test/framework/analyzer/daily_report_builder.py`
- **출력 파일**: `records/analysis/YYYY-MM-DD/daily_report.json`

---

## 🔄 버전 관리

- **v1**: 현재 버전 (고정)
- 스키마 변경 시 버전 업데이트 필요

---

## 📝 참고 사항

1. **절대 해석 없음**: 모든 필드는 사실만 기록
2. **구조 정보만**: 가격, 수익, 판단 제외
3. **계약 기반**: 데이터 저장용이 아닌 표준 스키마
4. **확장 가능**: ManualNotes로 사람 입력 영역 분리




