#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real-time I vs RF-frequency sweep

- DMM: Keithley 2000 (DC voltage read)
- RF source: HP E4432B (frequency set)

Default GPIB addresses follow existing lab scripts:
- Keithley 2000: GPIB43::19::INSTR
- HP E4432B:    GPIB43::26::INSTR
"""

import argparse
import csv
import signal
import time
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pyvisa

# ==================== User Settings (Spyder) ====================
# Spyder에서 주로 쓰실 값은 이 블록만 수정하면 됩니다.
USER_DMM_ADDRESS = "GPIB43::19::INSTR"
USER_RF_ADDRESS = "GPIB43::26::INSTR"

USER_START_HZ = 100e6
USER_STOP_HZ = 300e6
USER_STEP_HZ = 1e6

USER_TARGET_POWER_DBM = -10.0
# 현재 장비 파워값에서 USER_TARGET_POWER_DBM까지 step-wise ramp
USER_POWER_RAMP_STEP_DB = 0.5
USER_POWER_RAMP_DELAY_S = 0.15

# Current conversion: I[A] = GAIN_A_PER_V * DMM[V]
USER_GAIN_A_PER_V = 1e-9

USER_SETTLE_S = 0.2
USER_NPLC = 1.0
USER_AVERAGES = 1
USER_SAMPLE_DELAY_S = 0.02
USER_TIMEOUT_MS = 5000

# None이면 자동 파일명(I_vs_RF_YYYYMMDD_HHMMSS.csv) 사용
USER_OUTPUT_CSV = None
# None이면 CSV 이름 기준으로 자동 생성(예: I_vs_RF_xxx.png)
USER_OUTPUT_PNG = None


class GracefulStop:
    def __init__(self):
        self.stop_requested = False
        signal.signal(signal.SIGINT, self._request_stop)
        signal.signal(signal.SIGTERM, self._request_stop)

    def _request_stop(self, *_args):
        print("\nStop signal received. Finishing safely...")
        self.stop_requested = True


def parse_scpi_float(raw):
    text = str(raw).strip()
    if "," in text:
        text = text.split(",")[0]
    return float(text)


def make_sweep_points(start_hz, stop_hz, step_hz):
    if step_hz == 0:
        raise ValueError("step_hz must not be 0.")
    signed_step = abs(step_hz) if stop_hz >= start_hz else -abs(step_hz)
    points = np.arange(start_hz, stop_hz + signed_step * 0.5, signed_step, dtype=float)
    return points


class Keithley2000:
    def __init__(self, instrument, nplc=1.0):
        self.inst = instrument
        self.nplc = nplc
        self.configure()

    def configure(self):
        setup = [
            "*CLS",
            "*RST",
            ':SENS:FUNC "VOLT:DC"',
            ":SENS:VOLT:DC:RANG:AUTO ON",
            f":SENS:VOLT:DC:NPLC {self.nplc}",
            ":TRIG:SOUR IMM",
            ":TRIG:COUN 1",
            ":SAMP:COUN 1",
            ":FORM:ELEM READ",
            ":INIT:CONT ON",
        ]
        for cmd in setup:
            self.inst.write(cmd)
        time.sleep(0.2)

    def read_voltage(self, averages=1, sample_delay_s=0.02):
        values = []
        for idx in range(max(1, int(averages))):
            raw = self.inst.query("FETCh?")
            values.append(parse_scpi_float(raw))
            if idx < averages - 1 and sample_delay_s > 0:
                time.sleep(sample_delay_s)
        return float(np.mean(values))


class HPE4432B:
    def __init__(self, instrument):
        self.inst = instrument

    def set_frequency_hz(self, frequency_hz):
        self.inst.write(f"FREQ {frequency_hz}")

    def get_frequency_hz(self):
        return parse_scpi_float(self.inst.query("FREQ?"))

    def set_power_dbm(self, power_dbm):
        self.inst.write(f"POW {power_dbm}")

    def get_power_dbm(self):
        return parse_scpi_float(self.inst.query("POW?"))

    def ramp_power_dbm(self, target_dbm, step_db=0.5, delay_s=0.15):
        step_db = abs(float(step_db))
        if step_db == 0:
            raise ValueError("power ramp step must be > 0 dB")

        current = self.get_power_dbm()
        step_signed = step_db if target_dbm >= current else -step_db

        while abs(target_dbm - current) > step_db / 2:
            next_power = current + step_signed
            if step_signed > 0 and next_power > target_dbm:
                next_power = target_dbm
            elif step_signed < 0 and next_power < target_dbm:
                next_power = target_dbm

            self.set_power_dbm(next_power)
            current = next_power
            print(f"RF power ramp: {current:.3f} dBm")
            if delay_s > 0:
                time.sleep(delay_s)

        self.set_power_dbm(target_dbm)

def init_live_plot():
    plt.ion()
    fig, ax = plt.subplots(figsize=(9, 5))
    line, = ax.plot([], [], "o-", lw=1.5, ms=4)
    ax.set_title("Current vs RF Frequency")
    ax.set_xlabel("RF Frequency (MHz)")
    ax.set_ylabel("Current (nA)")
    ax.grid(True, alpha=0.35)
    fig.tight_layout()
    return fig, ax, line


def choose_current_scale(currents_a):
    if not currents_a:
        return 1e-9, "nA"

    max_abs = max(abs(v) for v in currents_a)
    if max_abs < 1e-6:
        return 1e-9, "nA"
    if max_abs < 1e-3:
        return 1e-6, "uA"
    if max_abs < 1:
        return 1e-3, "mA"
    return 1.0, "A"


def update_live_plot(fig, ax, line, x_mhz, y_a):
    scale_a, unit = choose_current_scale(y_a)
    y_scaled = [v / scale_a for v in y_a]
    line.set_data(x_mhz, y_scaled)
    ax.set_ylabel(f"Current ({unit})")
    ax.relim()
    ax.autoscale_view()
    fig.canvas.draw_idle()
    fig.canvas.flush_events()
    plt.pause(0.001)


def save_csv(filepath, rows):
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["time_s", "rf_frequency_hz", "dmm_voltage_v", "current_a"])
        writer.writerows(rows)


def make_png_path(csv_path, png_path=None):
    if png_path:
        return png_path
    if "." in csv_path:
        return f"{csv_path.rsplit('.', 1)[0]}.png"
    return f"{csv_path}.png"


def run(args):
    stopper = GracefulStop()
    rm = pyvisa.ResourceManager()

    dmm = None
    rf = None
    fig = None

    rows = []
    x_mhz = []
    y_a = []

    try:
        dmm = rm.open_resource(args.dmm_address)
        rf = rm.open_resource(args.rf_address)

        dmm.timeout = args.timeout_ms
        rf.timeout = args.timeout_ms

        k2000 = Keithley2000(dmm, nplc=args.nplc)
        src = HPE4432B(rf)

        # 출력 상태(ON/OFF)는 건드리지 않고, 현재 파워에서 목표 파워로만 ramp
        src.ramp_power_dbm(
            target_dbm=args.power_dbm,
            step_db=args.power_ramp_step_db,
            delay_s=args.power_ramp_delay_s,
        )

        points_hz = make_sweep_points(args.start_hz, args.stop_hz, args.step_hz)
        fig, ax, line = init_live_plot()

        print(f"Sweep points: {len(points_hz)}")
        print(f"DMM: {args.dmm_address}")
        print(f"RF : {args.rf_address}")
        print(
            f"Sweep range: {args.start_hz/1e6:.6f} -> {args.stop_hz/1e6:.6f} MHz "
            f"(step {abs(args.step_hz)/1e6:.6f} MHz)"
        )
        print(
            f"RF power target: {args.power_dbm:.3f} dBm "
            f"(ramp {args.power_ramp_step_db:.3f} dB/step)"
        )
        print(f"Current conversion gain: {args.gain_a_per_v:.3e} A/V")
        print("Press Ctrl+C to stop safely.\n")

        t0 = time.time()
        for idx, freq_hz in enumerate(points_hz, start=1):
            if stopper.stop_requested:
                break

            src.set_frequency_hz(freq_hz)
            time.sleep(args.settle_s)

            dmm_voltage_v = k2000.read_voltage(
                averages=args.averages,
                sample_delay_s=args.sample_delay_s,
            )
            current_a = args.gain_a_per_v * dmm_voltage_v
            elapsed_s = time.time() - t0

            rows.append([elapsed_s, float(freq_hz), dmm_voltage_v, current_a])
            x_mhz.append(float(freq_hz) / 1e6)
            y_a.append(current_a)

            update_live_plot(fig, ax, line, x_mhz, y_a)
            print(
                f"[{idx:4d}/{len(points_hz)}] "
                f"f = {freq_hz/1e6:10.6f} MHz, "
                f"Vdmm = {dmm_voltage_v:+.6e} V, "
                f"I = {current_a:+.6e} A"
            )

        save_csv(args.output_csv, rows)
        print(f"\nSaved: {args.output_csv}")

    finally:
        if fig is not None:
            png_path = make_png_path(args.output_csv, args.output_png)
            try:
                fig.savefig(png_path, dpi=200, bbox_inches="tight")
                print(f"Saved plot: {png_path}")
            except Exception as e:
                print(f"Warning: failed to save PNG plot ({e})")
            plt.ioff()
            plt.show()

        if dmm is not None:
            dmm.close()
        if rf is not None:
            rf.close()
        rm.close()


def build_arg_parser():
    default_csv = USER_OUTPUT_CSV or f"I_vs_RF_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    p = argparse.ArgumentParser(
        description="Measure DC current (Keithley 2000) while sweeping RF frequency (HP E4432B)."
    )
    p.add_argument("--dmm-address", default=USER_DMM_ADDRESS)
    p.add_argument("--rf-address", default=USER_RF_ADDRESS)
    p.add_argument("--start-hz", type=float, default=USER_START_HZ)
    p.add_argument("--stop-hz", type=float, default=USER_STOP_HZ)
    p.add_argument("--step-hz", type=float, default=USER_STEP_HZ)
    p.add_argument("--power-dbm", type=float, default=USER_TARGET_POWER_DBM)
    p.add_argument("--power-ramp-step-db", type=float, default=USER_POWER_RAMP_STEP_DB)
    p.add_argument("--power-ramp-delay-s", type=float, default=USER_POWER_RAMP_DELAY_S)
    p.add_argument("--gain-a-per-v", type=float, default=USER_GAIN_A_PER_V)
    p.add_argument("--settle-s", type=float, default=USER_SETTLE_S)
    p.add_argument("--nplc", type=float, default=USER_NPLC)
    p.add_argument("--averages", type=int, default=USER_AVERAGES)
    p.add_argument("--sample-delay-s", type=float, default=USER_SAMPLE_DELAY_S)
    p.add_argument("--timeout-ms", type=int, default=USER_TIMEOUT_MS)
    p.add_argument("--output-csv", default=default_csv)
    p.add_argument("--output-png", default=USER_OUTPUT_PNG)
    return p


if __name__ == "__main__":
    args = build_arg_parser().parse_args()
    run(args)
