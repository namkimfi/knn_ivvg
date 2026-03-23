# Quantum BO Hardware v4 코드 흐름 학습자료 (초보자용)

이 문서는 `Quantum_BO_Experiment_Hardware_v4.py`를 처음 보는 사람이,
"어디서 시작해서 어디로 흘러가는지"를 빠르게 이해하도록 만든 안내서입니다.

## 0) 이 코드가 하는 일 (한 줄 요약)

`n≈1`이 되는 최적 동작점 `(V_ENT, V_P, V_EXIT)`을 먼저 찾고(Phase 1),
그 주변을 2D로 정밀 맵핑해서 펌프 특성을 시각화/저장합니다(Phase 2).

---

## 1) 전체 흐름 한눈에 보기

```text
[Config 설정]
   ↓
[장비 연결 시도]
   ├─ 성공: Hardware mode
   └─ 실패/강제: Simulation mode
   ↓
[Phase 1: 3D 최적화]
   - 초기 랜덤 샘플
   - Bayesian Optimization
   - Early stopping
   - Plateau refinement (평탄한 n≈1 점 재선정)
   ↓
[사용자 확인(y/n/a)]
   ├─ y: Phase 2 진행
   ├─ n: 여기서 종료
   └─ a: 파라미터 수정 모드
   ↓
[Phase 2: 2D 맵핑]
   - LHS 초기 샘플
   - GP 불확실도 기반 adaptive 샘플
   ↓
[시각화 생성]
   ↓
[CSV/PNG 저장]
   ↓
[최종 요약 + 장비 종료]
```

---

## 2) 먼저 알아둘 핵심 개념 6개

1. `n`
   - 전자 펌핑 개수(사이클당 전자수)입니다.
   - 목표는 `n = 1`에 최대한 가깝게 만드는 것.

2. `target_current = e * f`
   - 이상적인 `n=1`일 때의 전류 기준값.
   - `n = measured_current / target_current`.

3. `Cost = log10(|n-1| + 1e-12)`
   - Phase 1에서 최소화하는 목표값.
   - 작을수록 `n`이 1에 가까움.

4. `Plateau refinement`
   - `|n-1|`만 작은 점이 아니라, `V_EXIT`를 약간 바꿔도 값이 크게 흔들리지 않는 "평탄한 점"을 최종점으로 선택.

5. `LHS (Latin Hypercube Sampling)`
   - Phase 2 시작 시 2D 영역을 고르게 찍는 초기 샘플링.

6. `Adaptive uncertainty sampling`
   - GP가 "가장 불확실하다"고 보는 지점을 추가 측정해서 맵 정확도를 빠르게 올림.

---

## 3) 코드 구조 지도 (어디를 먼저 읽어야 하는가)

`Quantum_BO_Experiment_Hardware_v4.py`의 추천 읽기 순서:

1. `Config` 클래스 (라인 61)
2. `InstrumentController` (라인 188)
3. `run_phase1_optimization` (라인 528)
4. `run_phase2_mapping` (라인 784)
5. 실행부(셀 10~15, 라인 1306 이후)

보조로 보면 좋은 부분:

- `BayesianOptimizer` (라인 380)
- `EfficientMapper` (라인 463)
- `save_all_data` (라인 1228)

---

## 4) Cell 기준 실행 흐름 상세

## Cell 1: Import

- 수치/최적화/시각화 라이브러리를 로드합니다.
- `pyvisa` import 성공 여부로 실제 장비 사용 가능성을 판단합니다.

## Cell 2: Config (가장 중요)

실험의 거의 모든 하이퍼파라미터가 여기에 모여 있습니다.

초보자가 먼저 조정할 가능성이 높은 항목:

- `FORCE_SIMULATION`:
  - `True`면 무조건 시뮬레이션 모드.
- `bounds_optimization`:
  - Phase 1에서 탐색할 `(V_ENT, V_P, V_EXIT)` 범위.
- `n_initial_points`, `n_iterations`, `early_stop_patience`
- `MAPPING_RANGE_V_ENT`, `MAPPING_RANGE_V_EXIT`
- `N_MAPPING_LHS`, `N_MAPPING_ADAPTIVE`

## Cell 3: InstrumentController

역할:

- 장비 연결 및 설정
- 전압 인가(`set_voltages`)
- 전류 측정 후 `n` 계산(`measure`)
- 시뮬레이션일 때는 모델 함수(`_simulate_n`)로 `n` 생성

핵심 포인트:

- 하드웨어 연결 실패 시 자동으로 simulation fallback.
- `measure()`가 실험 전체의 공통 측정 API 역할을 수행.

## Cell 4~5: 모델 클래스

- `BayesianOptimizer`:
  - Phase 1용 GP + EI 기반 다음 점 제안.
- `EarlyStopping`:
  - 일정 횟수 개선 없으면 중단.
- `EfficientMapper`:
  - Phase 2용 2D GP 모델.
  - LHS 샘플 생성 + 불확실도 최대점 추천.

## Cell 6: Phase 1 최적화 (`run_phase1_optimization`)

실제 루프:

1. 초기 `n_initial_points`개는 랜덤 측정.
2. 이후는 BO가 다음 점 제안.
3. 각 점에서 `n` 측정 후 cost 계산.
4. 필요 시 early stopping.
5. 종료 후 plateau refinement 수행:
   - `n≈1` 후보들에 대해 `V_EXIT ± dV` 재측정
   - `plateau_score = |n-1| + w * |Δn|`
   - 가장 평탄한 후보를 최종점으로 선택

결과 딕셔너리(`phase1_results`)에 저장되는 핵심:

- 최적점: `best_V_ent`, `best_V_p`, `best_V_exit`
- 성능: `best_n`, `best_cost`
- 이력: `X_hist`, `n_hist`, `y_hist`
- refinement 관련 메타데이터

## Cell 7: Phase 2 맵핑 (`run_phase2_mapping`)

입력:

- Phase 1 최적점

동작:

1. 최적점 중심으로 2D 범위 생성 (`V_ENT`, `V_EXIT`; `V_P`는 고정)
2. LHS로 초기 측정
3. GP fit
4. 반복적으로 불확실도 최대 지점 측정 + 재학습

결과(`phase2_results`) 핵심:

- `X_measured`, `n_measured`
- `bounds_2d`, `V_p_fixed`
- 학습된 `mapper` 객체

## Cell 8: 시각화

- Phase 1 요약 그래프
- Phase 2 6패널 맵:
  - `dI/dV_EXIT`, GP mean, uncertainty(or truth), error map, curve, line cut
- Combined summary 그래프

## Cell 9: 데이터 저장

저장 파일:

- `phase1_optimization_*.csv`
- `phase2_mapping_*.csv`
- `experiment_summary_*.csv`

## Cell 10~15: 실제 실행 오케스트레이션

- Cell 10: Phase 1 수행
- Cell 11: 사용자에게 진행 여부 입력받음(`y/n/a`)
- Cell 12~14: 조건부로 Phase 2, 플롯, 저장 수행
- Cell 15: 최종 요약 출력 + `instr.close()`

---

## 5) 초보자 실습 루틴 (추천)

1. `FORCE_SIMULATION = True`로 시작
2. `n_initial_points`, `n_iterations`를 작게 줄여 빠르게 1회 실행
3. Cell 10~15까지 순서대로 실행
4. 저장된 CSV에서 `best_n`, `best_V_*` 확인
5. 그 다음에만 하드웨어 모드로 전환

---

## 6) Phase 1 하이퍼파라미터: 검색 품질과 효율

아래 5개는 `run_phase1_optimization()`의 마지막 단계(plateau refinement) 품질을 크게 좌우합니다.

| 하이퍼파라미터 | 검색 품질(quality) 영향 | 검색 효율(efficiency) 영향 |
|---|---|---|
| `PHASE1_TARGET_N = 1.0` | BO/재선정이 "무엇을 정답으로 볼지"를 정의. 목표값이 물리적 목표와 맞을수록 최종점 품질이 좋아짐 | 목표 설정이 맞으면 불필요한 탐색 재시도를 줄여 전체 실험 시간을 절약 |
| `PHASE1_N_TOL = 0.03` | `n≈target` 후보로 인정하는 창(window). 너무 크면 plateau 가장자리 점이 섞일 수 있고, 너무 작으면 좋은 후보를 놓칠 수 있음 | 큰 값은 후보가 늘어 refinement 재측정이 증가, 작은 값은 계산량은 줄지만 재실행 위험 증가 |
| `PHASE1_PLATEAU_TOP_K = 8` | 재검증할 후보 개수. 클수록 "진짜 평탄한 점"을 찾을 확률 증가 | 후보 1개당 `V_EXIT±dV` 2회 추가 측정이 필요하므로, 대략 최대 `2*K`회 측정이 추가됨 |
| `PHASE1_DV_EXIT = 0.006` | 평탄도(`dn/dV_EXIT`)를 보는 간격. 너무 작으면 노이즈에 민감, 너무 크면 "국소(local) 평탄도"가 흐려짐 | 측정 횟수 자체는 동일하지만, 값이 부적절하면 잘못된 최적점 선택으로 후속 맵핑 품질이 떨어져 결과적으로 비효율 발생 |
| `PHASE1_FLATNESS_WEIGHT = 0.35` | `|n-1|` vs 평탄도 가중 균형. 크면 더 안정적인 plateau 내부점 선호, 작으면 n=1 근접도만 강하게 선호 | 적절한 가중치는 Phase 2 중심점을 안정화해 재실험 가능성을 줄임 |

### 6-1) 파라미터 상호작용 핵심

- `PHASE1_TARGET_N`은 "목표 중심"을 정하고, `PHASE1_N_TOL`은 그 주변 후보 폭을 정합니다.
- `PHASE1_PLATEAU_TOP_K`는 후보를 몇 개까지 다시 확인할지 정합니다.
- `PHASE1_DV_EXIT`는 각 후보의 평탄도 측정 품질을 결정합니다.
- `PHASE1_FLATNESS_WEIGHT`는 최종 선택 기준에서 "정확도(n=1 근접)"와 "안정성(평탄도)" 비중을 정합니다.

### 6-2) 실전 튜닝 가이드

- 증상: `best_n`은 1에 매우 가깝지만 재현성이 낮고 작은 바이어스 변화에 민감함
- 조정: `PHASE1_FLATNESS_WEIGHT`를 조금 올리고, `PHASE1_DV_EXIT`를 소폭 키워 평탄도 평가를 안정화

- 증상: early stopping 후에도 plateau 후보가 거의 없거나 refinement가 자주 스킵됨
- 조정: `PHASE1_N_TOL`을 약간 확대하거나 `PHASE1_PLATEAU_TOP_K`를 늘려 후보 풀 확보

- 증상: Phase 1 시간이 너무 길어짐
- 조정: `PHASE1_PLATEAU_TOP_K`를 줄이고, `PHASE1_N_TOL`을 너무 크게 잡지 않음

- 증상: 최종점이 n=1에서 자주 벗어남
- 조정: `PHASE1_FLATNESS_WEIGHT`를 너무 크게 두지 말고(과도한 평탄도 편향 방지), `PHASE1_TARGET_N`이 실험 목표와 일치하는지 재확인

### 6-3) 시뮬레이션 기준 추천 시작값/조정폭

아래 값은 현재 v4 로직 기준으로, "처음 실행 -> 안정화 튜닝"에 쓰기 좋은 실전 범위입니다.

| 하이퍼파라미터 | 추천 시작값 | 권장 조정 범위(시뮬레이션) | 한 번에 바꿀 권장 스텝 |
|---|---|---|---|
| `PHASE1_TARGET_N` | `1.0` | `0.98 ~ 1.02` (보정 필요 시에만) | `0.005 ~ 0.01` |
| `PHASE1_N_TOL` | `0.03` | `0.02 ~ 0.06` | `0.005 ~ 0.01` |
| `PHASE1_PLATEAU_TOP_K` | `8` | `5 ~ 12` | `±1 ~ ±2` |
| `PHASE1_DV_EXIT` | `0.006` | `0.004 ~ 0.012` V | `0.001 ~ 0.002` V |
| `PHASE1_FLATNESS_WEIGHT` | `0.35` | `0.20 ~ 0.60` | `0.05 ~ 0.10` |

빠른 적용 규칙:

- 재현성이 먼저면: `PHASE1_FLATNESS_WEIGHT`를 올리고, `PHASE1_DV_EXIT`를 소폭 확대
- 속도가 먼저면: `PHASE1_PLATEAU_TOP_K`를 줄이고, `PHASE1_N_TOL`을 과도하게 키우지 않기
- 후보 부족이면: `PHASE1_N_TOL`을 먼저 늘리고, 필요 시 `PHASE1_PLATEAU_TOP_K` 확대
- 튜닝은 한 번에 1개 파라미터만 변경 후 1회 실행 결과 비교 권장

---

## 7) 자주 헷갈리는 포인트

1. 왜 `best_idx_by_cost`와 `best_idx`가 다를 수 있나요?
   - `best_idx_by_cost`는 `|n-1|`만 본 점.
   - `best_idx`는 plateau 평탄성까지 반영한 최종점.

2. 왜 Phase 2에서 `V_P`를 고정하나요?
   - Phase 1에서 이미 최적 `V_P*`를 찾았다고 보고,
     2D 맵은 `V_ENT-V_EXIT` 평면만 집중 탐색하기 위해서입니다.

3. Early stopping이 뜨면 실패인가요?
   - 항상 실패는 아닙니다.
   - 개선이 멈췄다는 뜻이며, search 범위/노이즈/신호 상태를 재점검해야 합니다.

---

## 8) 디버깅 체크리스트

1. `PyVISA` import 실패 여부 확인
2. `FORCE_SIMULATION` 설정값 확인
3. `bounds_optimization`에 실제 plateau가 포함되는지 확인
4. `CURRENT_AMP_GAIN`이 장비 설정과 맞는지 확인
5. `SETTLING_TIME`이 너무 짧지 않은지 확인

---

## 9) 한 페이지 요약

- 이 코드는 "먼저 3D 최적점 찾기(Phase 1) -> 그 주변 2D 상세 맵(Phase 2)" 구조입니다.
- 모든 측정의 중심 함수는 `InstrumentController.measure()`.
- Phase 1은 정확도(`|n-1|`) + 안정성(plateau flatness) 기준으로 최종점을 고릅니다.
- Phase 2는 LHS + GP 불확실도 샘플링으로 측정 효율을 높입니다.
- 실행은 Cell 10~15가 담당하며, Cell 11에서 사용자가 분기(`y/n/a`)를 결정합니다.
