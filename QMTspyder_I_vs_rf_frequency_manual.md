# QMTspyder_I_vs_rf_frequency.py 매뉴얼

## 1) 목적
- RF source(HP E4432B)의 주파수를 스윕하면서,
- Keithley 2000 DMM으로 읽은 전압을 전류로 환산하여,
- `I vs RF frequency`를 실시간 플롯하고,
- Raw 데이터(`csv`) + 최종 플롯(`png`)을 저장합니다.

전류 환산식:
`I [A] = GAIN_A_PER_V * Vdmm [V]`

---

## 2) 장비/연결
- DMM: Keithley 2000
- RF Source: HP E4432B
- 기본 주소:
  - `GPIB43::19::INSTR` (DMM)
  - `GPIB43::26::INSTR` (RF)

코드 파일:
- `/Users/namkim/Documents/code for I-f/QMTspyder_I_vs_rf_frequency.py`

---

## 3) Spyder에서 사용자가 수정할 블록
아래 블록만 바꾸면 됩니다.

위치:
- `/Users/namkim/Documents/code for I-f/QMTspyder_I_vs_rf_frequency.py` 의 `User Settings (Spyder)` 블록

핵심 변수:
- `USER_START_HZ`, `USER_STOP_HZ`, `USER_STEP_HZ`
- `USER_TARGET_POWER_DBM`
- `USER_POWER_RAMP_STEP_DB`, `USER_POWER_RAMP_DELAY_S`
- `USER_GAIN_A_PER_V`
- `USER_OUTPUT_CSV`, `USER_OUTPUT_PNG`

예시:
```python
USER_START_HZ = 80e6
USER_STOP_HZ = 140e6
USER_STEP_HZ = 0.5e6

USER_TARGET_POWER_DBM = -10.0
USER_POWER_RAMP_STEP_DB = 0.5
USER_POWER_RAMP_DELAY_S = 0.15

USER_GAIN_A_PER_V = 1e-9

USER_OUTPUT_CSV = "I-f-10dBm.csv"
USER_OUTPUT_PNG = None
```

---

## 4) 논리 흐름 (실행 순서)
1. `run(args)` 시작
2. VISA ResourceManager 생성
3. DMM, RF 장비 오픈
4. DMM 설정
   - `VOLT:DC` 측정 모드
   - `FETCh?` 기반 읽기
5. RF 파워 램프
   - 현재 장비 파워(`POW?`)에서 목표 파워까지 step-wise 이동
   - 출력 ON/OFF 토글은 하지 않음
6. 주파수 포인트 배열 생성
   - `start -> stop`, `step` 방향 자동 처리
7. 실시간 플롯 초기화
8. 스윕 루프
   - RF 주파수 설정
   - settling 대기
   - DMM 전압 읽기(`FETCh?`)
   - `I = gain * Vdmm` 환산
   - 리스트/CSV row 누적
   - live plot 즉시 업데이트
9. 루프 종료 후 CSV 저장
10. 최종 플롯 PNG 저장
11. 장비 세션 close

---

## 5) 실시간 플롯 동작
- 측정 포인트가 추가될 때마다 같은 Figure를 갱신합니다.
- y축 단위는 전류 크기에 따라 자동으로 바뀝니다.
  - `nA`, `uA`, `mA`, `A`
- 즉, 스윕 완료 후 일괄 플롯이 아니라 측정 중 지속 업데이트입니다.

---

## 6) 파일 저장 규칙
CSV:
- `USER_OUTPUT_CSV = None` 이면 자동:
  - `I_vs_RF_YYYYMMDD_HHMMSS.csv`
- 문자열 지정 시 그 이름으로 저장
  - 예: `"I-f-0dBm.csv"`

PNG:
- `USER_OUTPUT_PNG = None` 이면 CSV 이름 기반 자동 생성
  - 예: CSV=`I-f-0dBm.csv` -> PNG=`I-f-0dBm.png`
- 문자열 지정 시 그 이름으로 저장

저장 데이터 컬럼(CSV):
- `time_s`
- `rf_frequency_hz`
- `dmm_voltage_v`
- `current_a`

---

## 7) 안전/운용 메모
- 코드가 RF 출력 ON/OFF를 강제하지 않습니다.
- 파워는 현재 값에서 목표값까지 step-wise로 이동합니다.
- 목표 파워를 바꿀 때는 `USER_POWER_RAMP_STEP_DB`, `USER_POWER_RAMP_DELAY_S`를 함께 조정해 소자 충격을 줄이세요.
- `gain` 값이 바뀌면 전류값 전체가 비례해서 바뀌므로 실험 셋업에 맞춰 반드시 확인하세요.

---

## 8) 자주 발생하는 실수
- 파일명 문자열에 따옴표 누락
  - 잘못된 예: `USER_OUTPUT_CSV = I-f-0dBm`
  - 올바른 예: `USER_OUTPUT_CSV = "I-f-0dBm.csv"`
- `.csv`, `.png` 확장자 누락
- gain 단위 착오 (`A/V`인지 재확인)

---

## 9) 빠른 체크리스트
- GPIB 주소 맞는지
- 목표 주파수 범위/스텝 맞는지
- 목표 파워 및 램프 스텝/지연 적절한지
- `USER_GAIN_A_PER_V` 값 맞는지
- 저장 파일명 설정했는지 (`CSV`, `PNG`)

