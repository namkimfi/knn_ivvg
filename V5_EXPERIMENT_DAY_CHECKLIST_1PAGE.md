# v5 실험 당일 1페이지 체크시트

문서 목적: `Quantum_BO_Experiment_Hardware_v5.ipynb`를 당일 실험에서 빠르게, 실수 없이 실행하기 위한 1장 요약.

---

## 0) 실험 기본 정보

- 날짜/시간: `____________________`
- 샘플/칩 ID: `____________________`
- 실험자: `____________________`
- 노트북 파일: `Quantum_BO_Experiment_Hardware_v5.ipynb`

---

## 1) 시작 전 60초 체크

- [ ] 케이블/접지/바이어스 라인 연결 확인
- [ ] GPIB 주소(`ADDR_*`) 실제 장비와 일치 확인
- [ ] 펌프 주파수 `f` 값 확인 (실장비 설정과 일치)
- [ ] Rule No.1 확인: `MAX_VOLTAGE_STEP_V < 0.005 V` (기본 `0.004 V`)
- [ ] Phase 1/2 gain 다이얼: `1e-7 A/V`
- [ ] Phase 3 이후 목표 gain 다이얼: `1e-9 A/V`
- [ ] 테스트 모드 여부 확인: `FORCE_SIMULATION` (`False`가 실험 권장)

---

## 2) 오늘 조정할 하이퍼파라미터 기록

| 항목 | 오늘 값 | 권장 시작값 | 메모 |
|---|---:|---:|---|
| `PINCH_SCAN_RANGES['V_ent']` |  | `(-0.3, 0.3)` | |
| `PINCH_SCAN_RANGES['V_p']` |  | `(-0.3, 0.3)` | |
| `PINCH_SCAN_RANGES['V_exit']` |  | `(-0.3, 0.3)` | |
| `PINCH_SCAN_POINTS` |  | `121` | |
| `PINCH_REF_V_ENT / V_P / V_EXIT` |  | `0.0 / 0.0 / 0.0` | |
| `PINCH_OFF_THRESHOLD_A` |  | `0.5e-9` | |
| `PHASE2_RANGE_V_ENT` |  | `0.20` | 총 폭(total) |
| `PHASE2_RANGE_V_EXIT` |  | `0.40` | 총 폭(total) |
| `PHASE2_GRID_N` |  | `31` | `N x N` |
| `PHASE2_I_MIN_A` |  | `0.0` | strict: `I > min` |
| `PHASE2_I_MAX_A` |  | `4e-9` | strict: `I < max` |
| `PHASE4_N_INITIAL` |  | `20` | |
| `PHASE4_N_ITER` |  | `80` | |
| `PHASE4_EARLY_STOP_PATIENCE` |  | `25` | |
| `PHASE4_VP_WINDOW` |  | `0.12` | total |
| `PHASE4_N_TOL` |  | `0.03` | |
| `PHASE4_PLATEAU_TOP_K` |  | `8` | |
| `PHASE4_DV_EXIT` |  | `0.006` | plateau 짧으면 `0.002~0.003` 고려 |
| `PHASE4_FLATNESS_WEIGHT` |  | `0.35` | |
| `N_MAPPING_LHS` |  | `30` | |
| `N_MAPPING_ADAPTIVE` |  | `70` | |

---

## 3) 실행 순서 체크 (Cell 10 → 15)

- [ ] **Cell 10 실행**: Phase 1 + Phase 2(Attempt 1)
- [ ] **Cell 11 실행 (Phase 3 결정)**:
  - [ ] `y`: 승인 후 gain 다이얼 `1e-9 A/V` 수동 전환, Enter
  - [ ] `n`: 중단 경로
  - [ ] `r`: Phase 2 재시도
- [ ] **Cell 12 실행**: Phase 4 (`n=1` constrained BO)
- [ ] **Cell 13 실행**: Phase 5 진행 여부 `y/n`
- [ ] **Cell 14 실행**: 저장
- [ ] **Cell 15 실행**: 최종 요약 + 장비 close

---

## 4) Phase별 통과 판단 기준 (간단)

### Phase 1 (pinch-off)
- [ ] 3개 게이트 모두 sweep 완료
- [ ] pinch-off 전압이 비정상 끝점으로만 몰리지 않음
- [ ] 곡선/임계값이 현재 전류 스케일과 논리적으로 맞음

### Phase 2 (`0 < I < 4 nA`)
- [ ] `valid_points_connected > 0`
- [ ] 유효 bounds가 물리적으로 말이 됨
- [ ] 필요 시 `r`로 1~2회 재시도

### Phase 3 (수동 gain 전환)
- [ ] 다이얼 실제 `1e-9 A/V` 전환 완료
- [ ] Enter 이후 소프트 gain 동기화 메시지 확인

### Phase 4 (`n=1` 탐색)
- [ ] `best_n`, `|n-1|`, refinement 상태 확인
- [ ] plateau 폭이 짧으면 `PHASE4_DV_EXIT` 재조정 검토

### Phase 5 (pump map)
- [ ] 6-panel 플롯 생성 확인
- [ ] 측정점 수가 `N_MAPPING_LHS + N_MAPPING_ADAPTIVE`와 일치

---

## 5) 자주 막히는 경우 빠른 대응

- Phase 1이 평평함:
  - [ ] `PINCH_SCAN_RANGES` 동작영역으로 이동
  - [ ] `PINCH_OFF_THRESHOLD_A` 신호 스케일에 맞게 조정
- Phase 2 유효영역 없음:
  - [ ] `PHASE2_RANGE_V_ENT/EXIT` 확대
  - [ ] `PHASE2_GRID_N` 증가
  - [ ] `PHASE2_I_MAX_A` 기준 재검토
- Phase 4 불안정:
  - [ ] `PHASE4_N_INITIAL`, `PHASE4_N_ITER` 증가
  - [ ] `PHASE4_DV_EXIT`/`PHASE4_FLATNESS_WEIGHT` 조정

---

## 6) 종료 전 파일 확인

- [ ] `phase1_pinchoff_*.csv/png`
- [ ] `phase2_attempt_*.csv` 및 attempt별 plot
- [ ] `phase4_optimization_*.csv` (진행 시)
- [ ] `phase5_mapping_*.csv`, `phase5_pump_maps_*.png` (진행 시)
- [ ] `experiment_summary_v5_*.csv`
- [ ] 출력 폴더 백업 완료

