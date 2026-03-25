"""
Keithley 2000 NPLC 설정 스크립트

사용법: 아래 설정값만 바꾸고 실행하세요!
필요 패키지: pip install pyvisa pyvisa-py
"""

import pyvisa

# ============================================================
#   여기만 수정하세요
# ============================================================
NPLC = 5                          # 원하는 NPLC 값 (0.01, 0.1, 1, 5, 10)
GPIB_ADDRESS = "GPIB0::16::INSTR"  # 장비 GPIB 주소
# ============================================================

rm = pyvisa.ResourceManager()
dmm = rm.open_resource(GPIB_ADDRESS)
dmm.write_termination = "\n"
dmm.read_termination = "\n"
dmm.timeout = 10000

# 장비 확인
idn = dmm.query("*IDN?").strip()
print(f"장비: {idn}")

# NPLC 설정
dmm.write(f":SENS:VOLT:DC:NPLC {NPLC}")
print(f"NPLC {NPLC}(으)로 설정 완료")

# 설정값 확인
result = dmm.query(":SENS:VOLT:DC:NPLC?").strip()
print(f"확인: 현재 NPLC = {result}")

dmm.close()
rm.close()
