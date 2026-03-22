# Quantum BO Hardware v5 코드 흐름 학습자료 (실험자용)

이 문서는 `Quantum_BO_Experiment_Hardware_v5.ipynb`를 처음 실행하거나,
실험 상황에 맞춰 하이퍼파라미터를 손으로 조정할 때 바로 참고할 수 있도록 만든 매뉴얼입니다.

## 0) 이 코드가 하는 일 (한 줄 요약)

Phase 1~5 순서로,

1. pinch-off 전압 탐색
2. `0 < I < 4 nA` 유효 영역 탐색
3. 실험자 수동 gain 전환
4. 제약 BO로 `n=1` 동작점 탐색
5. pump map 생성

을 수행합니다.

---

## 1) v5 핵심 규칙과 이전 버전 대비 차이

### Rule No.1 (필수)
- 모든 전압 변경은 step-wise.
- 코드 강제값: `MAX_VOLTAGE_STEP_V = 0.004 V` (4 mV)
- 즉, 한 번에 4 mV보다 큰 점프는 자동 분할 이동됩니다.

### 수동 개입 포인트
- Phase 3에서 실험자가 전류 앰프 gain 다이얼을 직접 `1e-9 A/V`로 전환해야 합니다.
- 전환 후 Enter를 눌러야 Phase 4로 진행됩니다.

### 시뮬레이션 관련 주의
- 하드웨어 연결 실패 또는 `FORCE_SIMULATION=True`면 자동 시뮬레이션 모드입니다.
- 현재 시뮬레이터는 pump 모델 기반이므로, Phase 1의 pinch-off 곡선 형태가 실장비와 다를 수 있습니다.

---

## 2) 전체 실행 흐름

```text
[Cell 2: Config 세팅]
   ↓
[Cell 10]
  - 장비 연결(실패 시 simulation)
  - Phase 1: pinch-off
  - Phase 2: positive current region (attempt 1)
   ↓
[Cell 11: Phase 3 의사결정 y/n/r]
  - y: 수동 gain 전환(1e-9) → Phase 4
  - n: 즉시 종료 경로
  - r: Phase 2 재시도 누적
   ↓
[Cell 12]
  - Phase 4: constrained BO (n≈1)
   ↓
[Cell 13]
  - Phase 5 진행 여부(y/n)
  - y면 pump map 수행
   ↓
[Cell 14]
  - CSV/요약 저장
   ↓
[Cell 15]
  - 최종 요약 + 장비 종료
```

---

## 3) Cell별 역할

### Cell 1: Imports
- 수치/최적화/시각화 라이브러리 import
- `pyvisa` import 성공 여부 확인

### Cell 2: Config
- 실험자가 손으로 조정하는 모든 주요 파라미터 위치

### Cell 3: InstrumentController
- 장비 연결
- `set_voltages_stepwise()`로 4 mV step 규칙 강제
- `set_current_amp_gain()`으로 소프트 gain 동기화

### Cell 4: BayesianOptimizer / EarlyStopping
- Phase 4 BO 엔진

### Cell 5: EfficientMapper
- Phase 5 map 학습 엔진

### Cell 6
- `run_phase1_pinchoff()`
- `run_phase4_optimization()`

### Cell 7
- `run_phase2_positive_current_mapping()`
- `run_phase5_mapping()`

### Cell 8
- Phase 1/2/4/5 시각화 함수

### Cell 9
- `save_all_data_v5()` 저장 함수

### Cell 10~15
- 실제 실행 orchestration

---

## 4) 실험자가 손으로 세팅하는 하이퍼파라미터 전체 설명

아래는 `Config` 기준 전수 목록입니다.

## 4-1) 물리 상수/기준

| 파라미터 | 기본값 | 단위 | 의미 | 실험 영향 | 튜닝 가이드 |
|---|---:|---|---|---|---|
| `e` | `1.60217663e-19` | C | 전자 전하 | `target_current = e*f` 계산에 사용 | 보통 고정 |
| `f` | `8e7` | Hz | 펌프 주파수 | `n = I/(ef)` 계산의 기준 | 실제 구동 주파수와 반드시 일치 |
| `target_current` | `e*f` | A | `n=1` 기준 전류 | Phase 4/5의 n 해석 기준 | 직접 수정 X (e, f로 결정) |

## 4-2) Gain 정책

| 파라미터 | 기본값 | 단위 | 의미 | 실험 영향 | 튜닝 가이드 |
|---|---:|---|---|---|---|
| `GAIN_PHASE1_A_PER_V` | `1e-7` | A/V | Phase 1 측정 gain | pinch-off 전류 스케일 | 장비 다이얼과 맞춰야 함 |
| `GAIN_PHASE2_A_PER_V` | `1e-7` | A/V | Phase 2 측정 gain | `0<I<4nA` 판정 정확도 | Phase 2 다이얼과 일치 |
| `GAIN_PHASE4_A_PER_V` | `1e-9` | A/V | Phase 4/5 gain | `n=1` 근처 고해상 측정 | Phase 3 수동 전환값과 일치 |
| `CURRENT_AMP_GAIN` | `GAIN_PHASE1_A_PER_V` | A/V | 초기 소프트 gain | 초기 측정 스케일 | 보통 직접 수정 대신 phase gain 값 수정 |

참고:
- Cell 11에서 `y` 선택 시 `set_current_amp_gain(GAIN_PHASE4_A_PER_V)`가 자동 호출됩니다.

## 4-3) 전압 이동 규칙

| 파라미터 | 기본값 | 단위 | 의미 | 실험 영향 | 튜닝 가이드 |
|---|---:|---|---|---|---|
| `MAX_VOLTAGE_STEP_V` | `0.004` | V | 한 step 최대 전압 변화량 | 과도 응답/충격 억제 | Rule No.1 때문에 `0.005` 미만 유지 |
| `SETTLING_TIME` | `0.08` | s | 각 step 이후 대기시간 | 안정성 vs 속도 | 노이즈 크면 증가, 너무 느리면 감소 |

## 4-4) GPIB 주소

| 파라미터 | 기본값 | 의미 | 튜닝 가이드 |
|---|---|---|---|
| `ADDR_YOKO_ENT` | `GPIB43::1::INSTR` | Entrance gate source 주소 | 장비 주소와 다르면 연결 실패 |
| `ADDR_YOKO_P` | `GPIB43::2::INSTR` | Plunger gate source 주소 | 장비 주소와 맞춤 |
| `ADDR_YOKO_EXIT` | `GPIB43::8::INSTR` | Exit gate source 주소 | 장비 주소와 맞춤 |
| `ADDR_DMM` | `GPIB43::19::INSTR` | DMM 주소 | DMM 주소와 맞춤 |

## 4-5) Phase 1: Pinch-off

| 파라미터 | 기본값 | 단위 | 의미 | 실험 영향 | 튜닝 가이드 |
|---|---:|---|---|---|---|
| `PINCH_SCAN_RANGES['V_ent']` | `(-0.3, 0.3)` | V | V_ENT sweep 범위 | 곡선이 안 보이면 범위 미스 가능 | 장비 동작 영역 중심으로 재설정 |
| `PINCH_SCAN_RANGES['V_p']` | `(-0.3, 0.3)` | V | V_P sweep 범위 | 동일 | 동일 |
| `PINCH_SCAN_RANGES['V_exit']` | `(-0.3, 0.3)` | V | V_EXIT sweep 범위 | 동일 | 동일 |
| `PINCH_SCAN_POINTS` | `121` | count | 게이트당 샘플 점 수 | 해상도 vs 시간 | 빠른 테스트: 41~81, 본실험: 101~201 |
| `PINCH_REF_V_ENT` | `0.0` | V | 다른 게이트 고정값(ENT 기준) | cross-coupling 영향 | 장치 기준점으로 이동 추천 |
| `PINCH_REF_V_P` | `0.0` | V | 다른 게이트 고정값(P 기준) | 동일 | 동일 |
| `PINCH_REF_V_EXIT` | `0.0` | V | 다른 게이트 고정값(EXIT 기준) | 동일 | 동일 |
| `PINCH_OFF_THRESHOLD_A` | `0.5e-9` | A | \\|I\\| 임계값 crossing 기준 | 너무 크면 시작점이 pinch-off로 선택됨 | 실제 전류 스케일보다 충분히 작게 설정 |

Phase 1 선택 로직:
- sweep 중 `|I| <= threshold`를 처음 만족하는 전압을 pinch-off로 선택
- crossing이 없으면 `|I|` 최소점 fallback

## 4-6) Phase 2: Positive-current 영역 탐색

| 파라미터 | 기본값 | 단위 | 의미 | 실험 영향 | 튜닝 가이드 |
|---|---:|---|---|---|---|
| `PHASE2_RANGE_V_ENT` | `0.20` | V (total) | V_ENT 탐색 총 폭 | 좁으면 영역 누락, 넓으면 시간 증가 | 초기 넓게, 안정화 후 축소 |
| `PHASE2_RANGE_V_EXIT` | `0.40` | V (total) | V_EXIT 탐색 총 폭 | 동일 | 동일 |
| `PHASE2_GRID_N` | `31` | count/axis | 2D grid 해상도 (`N x N`) | 경계 정확도 vs 시간 | 21(빠름), 31(균형), 41(정밀) |
| `PHASE2_I_MIN_A` | `0.0` | A | 조건 하한 (`I > min`) | 양전류 판정 | 일반적으로 0 유지 |
| `PHASE2_I_MAX_A` | `4e-9` | A | 조건 상한 (`I < max`) | 유효영역 크기 결정 | 요구 기준에 따라 조정 |

주의:
- 조건은 strict inequality: `0 < I < 4 nA`
- raw mask에서 가장 큰 연결 컴포넌트만 최종 유효영역으로 사용

## 4-7) Phase 4: Constrained BO (`n=1`)

| 파라미터 | 기본값 | 단위 | 의미 | 실험 영향 | 튜닝 가이드 |
|---|---:|---|---|---|---|
| `PHASE4_TARGET_N` | `1.0` | - | 목표 n 값 | objective 중심 | 보통 1.0 고정 |
| `PHASE4_N_INITIAL` | `20` | count | 랜덤 초기 샘플 수 | 탐색 안정성 vs 시간 | 노이즈 크면 증가 |
| `PHASE4_N_ITER` | `80` | count | BO 반복 최대 횟수 | 품질 vs 시간 | 빠른 실험 시 감소 |
| `PHASE4_EARLY_STOP_PATIENCE` | `25` | count | 개선 없을 때 조기종료 기준 | 과도 탐색 방지 | 너무 작으면 조기 중단 위험 |
| `PHASE4_VP_WINDOW` | `0.12` | V (total) | V_P 탐색 폭(phase1 중심) | V_P 자유도 조절 | 좁히면 안정/빠름, 넓히면 탐색 폭 증가 |
| `PHASE4_N_TOL` | `0.03` | - | plateau 후보로 인정할 `|n-1|` 창 | 후보 수 제어 | 후보 부족 시 증가 |
| `PHASE4_PLATEAU_TOP_K` | `8` | count | refinement 후보 개수 상한 | 재측정 횟수 증가 | 시간 부족 시 감소 |
| `PHASE4_DV_EXIT` | `0.006` | V | 평탄도 평가용 ±dV | plateau 폭이 짧으면 과대평가 위험 | 짧은 plateau면 `0.002~0.003` 고려 |
| `PHASE4_FLATNESS_WEIGHT` | `0.35` | - | 평탄도 가중치 | 안정성 vs 정확도 균형 | 재현성 낮으면 증가 |

Phase 4의 plateau 점수:
- `plateau_score = |n_center - 1| + w * |n_plus - n_minus|`
- 여기서 `w = PHASE4_FLATNESS_WEIGHT`
- score 최소점을 최종 operating point로 선택

## 4-8) Phase 5: Pump map

| 파라미터 | 기본값 | 단위 | 의미 | 실험 영향 | 튜닝 가이드 |
|---|---:|---|---|---|---|
| `MAPPING_RANGE_V_ENT` | `0.2` | V (total) | 최종 map의 V_ENT 총 폭 | 시야 vs 해상도 | plateau 주변 위주면 축소 |
| `MAPPING_RANGE_V_EXIT` | `0.40` | V (total) | 최종 map의 V_EXIT 총 폭 | 동일 | 동일 |
| `N_MAPPING_LHS` | `30` | count | 초기 LHS 샘플 수 | 초기 커버리지 | 노이즈 크면 증가 |
| `N_MAPPING_ADAPTIVE` | `70` | count | adaptive 샘플 수 | map 정밀도 | 시간 부족 시 감소 |
| `MAPPING_GRID_RESOLUTION` | `80` | count/axis | 시각화 격자 해상도 | 그림 정밀도/연산량 | 느리면 40~60 |
| `TRANSCONDUCTANCE_CLIP_PERCENTILE` | `99.0` | % | dI/dV 색상 클리핑 | 시각화 대비 | 노이즈 과하면 95~98 |
| `CURVE_OFFSETS` | `[-0.04,-0.02,0.02,0.04]` | V | line cut용 V_ENT 오프셋 | 비교 곡선 위치 | 영역 폭에 맞춰 조정 |

## 4-9) 모드/출력

| 파라미터 | 기본값 | 의미 | 튜닝 가이드 |
|---|---|---|---|
| `FORCE_SIMULATION` | `False` | `True`면 장비 유무와 무관하게 simulation | 로직 점검 시 `True` 추천 |
| `timestamp` | 자동 생성 | 출력 파일 시간 태그 | 보통 수정 X |
| `output_dir` | `./experiment_outputs_v5_<timestamp>` | 결과 저장 폴더 | 경로 정책에 맞게 변경 가능 |

---

## 5) 수동 입력(하이퍼파라미터 외, 실행 중 결정값)

## 5-1) Phase 3 (Cell 11)
- 입력: `y / n / r`
- `y`: 승인 + 수동 gain 전환 후 진행
- `n`: 즉시 중단 경로
- `r`: 동일 설정으로 Phase 2 재시도

## 5-2) Phase 5 gate (Cell 13)
- 입력: `y / n`
- `y`: pump map 실행
- `n`: Phase 5 스킵하고 저장/요약

---

## 6) 실험 시작 전 체크리스트

1. GPIB 주소가 실제 장비와 일치하는지 확인 (`ADDR_*`).
2. 주파수 `f`가 실제 설정과 일치하는지 확인.
3. Phase 1/2 gain 다이얼이 `1e-7`, Phase 3 이후 `1e-9`로 바뀌는지 확인.
4. `MAX_VOLTAGE_STEP_V < 0.005` 규칙 유지 확인.
5. `PINCH_SCAN_RANGES`와 `PINCH_OFF_THRESHOLD_A`가 장치 전류 스케일에 맞는지 확인.

---

## 7) 대표 튜닝 시나리오

## 7-1) Phase 1 그래프가 평평하게 보일 때
- 원인 후보:
  - 스캔 범위가 동작 영역 밖
  - `PINCH_OFF_THRESHOLD_A`가 실제 신호보다 너무 큼
- 조치:
  - `PINCH_SCAN_RANGES`를 장치 동작 전압 근처로 이동
  - `PINCH_OFF_THRESHOLD_A`를 신호 스케일에 맞게 낮춤

## 7-2) Phase 2 유효영역이 너무 작거나 없음
- 조치:
  - `PHASE2_RANGE_V_ENT`, `PHASE2_RANGE_V_EXIT` 확대
  - `PHASE2_GRID_N`를 높여 경계 포착 개선
  - 필요시 `PHASE2_I_MAX_A` 기준 완화

## 7-3) Phase 4가 불안정하거나 재현성 낮을 때
- 조치:
  - `PHASE4_N_INITIAL`, `PHASE4_N_ITER` 소폭 증가
  - `PHASE4_FLATNESS_WEIGHT` 소폭 증가
  - plateau 폭이 짧으면 `PHASE4_DV_EXIT` 축소

## 7-4) 전체 실행이 너무 느릴 때
- 조치 우선순위:
  - `PHASE2_GRID_N` 감소
  - `N_MAPPING_ADAPTIVE` 감소
  - `PINCH_SCAN_POINTS` 감소
  - `SETTLING_TIME` 최소한으로 조정

---

## 8) 출력 파일 구조

기본 출력 폴더: `experiment_outputs_v5_<timestamp>/`

주요 결과:
- `phase1_pinchoff_<gate>_<timestamp>.csv`
- `phase2_attempt_<k>_<timestamp>.csv` (재시도별)
- `phase4_optimization_<timestamp>.csv` (Phase 4 수행 시)
- `phase5_mapping_<timestamp>.csv` (Phase 5 수행 시)
- `phase1_pinchoff_*.png`, `phase2_positive_region_attempt*.png`, `phase4_summary_*.png`, `phase5_pump_maps_*.png`
- `experiment_summary_v5_<timestamp>.csv`

---

## 9) 빠른 시작 권장 프로파일

## 9-1) 로직 점검(시뮬레이션)
- `FORCE_SIMULATION = True`
- `PINCH_SCAN_POINTS = 41`
- `PHASE2_GRID_N = 21`
- `PHASE4_N_INITIAL = 8`, `PHASE4_N_ITER = 20`
- `N_MAPPING_LHS = 10`, `N_MAPPING_ADAPTIVE = 20`

## 9-2) 실험 본측정(하드웨어)
- `FORCE_SIMULATION = False`
- gain 다이얼 전환 절차 엄수
- `MAX_VOLTAGE_STEP_V` 유지
- Phase 3에서 필요 시 `r`로 Phase 2 재시도 후 best attempt 선택

---

## 10) 마지막 정리

이 v5는
- step-wise 전압 규칙,
- Phase 3 수동 gain 전환,
- Phase 2 재시도(`r`) 이력 저장,
- Phase 4 제약 BO,
- Phase 5 pump map

을 포함한 실험 워크플로우 버전입니다.

하이퍼파라미터는 반드시 한 번에 하나씩 바꾸고,
각 변경 후 결과(유효영역 크기, best n, 재현성)를 비교해 누적 튜닝하는 것을 권장합니다.
