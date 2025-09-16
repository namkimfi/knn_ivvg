# -*- coding: utf-8 -*-
"""
Created on Tue Sep 16 12:08:48 2025

@author: SEQD-RFSET
"""

# -*- coding: utf-8 -*-
"""
Created on Thu Sep 11 15:47:24 2025

@author: SEQD-RFSET
"""

#!/usr/bin/env python
# coding: utf-8

#Claude ;double loop with sweeep function
#save file by IHLee

import pyvisa
import time
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import clear_output
import re  # Regular expressions module

# GPIB addresses
yokoid8 = "GPIB43::8::INSTR"
yokoid1 = "GPIB43::1::INSTR"
yokoid2 = "GPIB43::2::INSTR"
yokoid7 = "GPIB43::7::INSTR"
yokoid4 = "GPIB43::4::INSTR"
yokoid5 = "GPIB43::5::INSTR"
yokoid6 = "GPIB43::6::INSTR"
yokoid10 = "GPIB43::10::INSTR"
dmmid = "GPIB43::19::INSTR"
E4432B_address = "GPIB43::26::INSTR"

# Function to open resource
def open_resource(resource_id):
    rm = pyvisa.ResourceManager()
    return rm.open_resource(resource_id)

def append_multiple_lines(file_name, lines_to_append):
    with open(file_name, "a+") as file_object:
        appendEOL = False
        file_object.seek(0)
        data = file_object.read(100)
        if len(data) > 0:
            appendEOL = True
        for line in lines_to_append:
            if appendEOL == True:
                file_object.write("\n")
            else:
                appendEOL = True
            file_object.write(line)

# RF Functions
def present_freq(instrument):
    try:
        response = instrument.query("FREQ?")
        match = re.search(r'([+-]?\d+\.?\d*E?[+-]?\d*)', response)
        if match:
            return float(match.group(1))
        else:
            raise ValueError(f"Unexpected response format: {response}")
    except Exception as e:
        print(f"Error retrieving freq: {e}")
        return None

def windup_freq(instrument, target_freq, step_size, delay):
    present_freq_val = present_freq(instrument)
    if present_freq_val is None: return
    step_size = abs(step_size) if present_freq_val < target_freq else -abs(step_size)
    while abs(present_freq_val - target_freq) > abs(step_size) / 2:
        new_freq = present_freq_val + step_size
        new_freq = target_freq if (step_size > 0 and new_freq > target_freq) or (step_size < 0 and new_freq < target_freq) else new_freq
        instrument.write(f'FREQ {new_freq}')
        print(f"Ramping frequency to: {new_freq/1e6:.3f} MHz")
        time.sleep(delay)
        present_freq_val = present_freq(instrument)
    instrument.write(f'FREQ {target_freq}')
    print(f"Final frequency set to: {target_freq/1e6:.3f} MHz")


def present_Prf(instrument):
    try:
        response = instrument.query("POW?")
        match = re.search(r'([+-]?\d+\.?\d*E?[+-]?\d*)', response)
        if match:
            return float(match.group(1))
        else:
            raise ValueError(f"Unexpected response format: {response}")
    except Exception as e:
        print(f"Error retrieving power: {e}")
        return None

def windup_Prf(instrument, target_power, step_size, delay):
    present_power_val = present_Prf(instrument)
    if present_power_val is None: return
    step_size = abs(step_size) if present_power_val < target_power else -abs(step_size)
    while abs(present_power_val - target_power) > abs(step_size) / 2:
        new_power = present_power_val + step_size
        new_power = target_power if (step_size > 0 and new_power > target_power) or (step_size < 0 and new_power < target_power) else new_power
        instrument.write(f'POW {new_power}')
        print(f"Ramping power to: {new_power:.3f} dBm")
        time.sleep(delay)
        present_power_val = present_Prf(instrument)
    instrument.write(f'POW {target_power}')
    print(f"Final power set to: {target_power:.3f} dBm")

# Function to read present voltage
def present_voltage(instrument):
    response = instrument.query("OD")
    match = re.search(r'([+-]?\d+\.\d+E[+-]\d+)', response)
    if match:
        return float(match.group(1))
    else:
        raise ValueError(f"Unexpected response format: {response}")

# Function to wind up voltage
def windup_voltage(instrument, start_voltage, step_size, delay):
    present_voltage_val = present_voltage(instrument)
    step_size = abs(step_size) if present_voltage_val < start_voltage else -abs(step_size)
    while abs(present_voltage_val - start_voltage) > abs(step_size) / 2:
        new_voltage = present_voltage_val + step_size
        new_voltage = start_voltage if (step_size > 0 and new_voltage > start_voltage) or (step_size < 0 and new_voltage < start_voltage) else new_voltage
        instrument.write(f"S{new_voltage:.6f}E")
        print(f"Wind-up voltage to: {new_voltage:.6f} V")
        time.sleep(delay)
        present_voltage_val = present_voltage(instrument)
    instrument.write(f"S{start_voltage:.6f}E")
    print(f"Final voltage set to: {start_voltage:.6f} V")

# Function to sweep voltage and measure current
def sweep_V1(instrument, dmm, start_voltage, target_voltage, step_size, delay):
    present_voltage_val = start_voltage
    currents, voltages = [], []
    step_size = abs(step_size) if present_voltage_val < target_voltage else -abs(step_size)
    num_steps = int(np.round(abs(target_voltage - start_voltage) / abs(step_size)))
    
    for i in range(num_steps + 1):
        new_voltage = start_voltage + i * step_size
        instrument.write(f"S{new_voltage:.6f}E")
        # No print here to reduce console clutter during sweep
        time.sleep(delay)
        
        actual_voltage = present_voltage(instrument)
        voltages.append(actual_voltage)
        
        current = float(dmm.query("fetch?"))
        currents.append(current)
       
        # Live plotting inside the loop
        clear_output(wait=True)
        plt.figure(figsize=(10, 6))
        plt.plot(voltages, currents, 'b-o', label='Live I-V Data')
        plt.title("Live I-V Sweep")
        plt.xlabel("Voltage (Vx)")
        plt.ylabel("Current (A)")
        plt.grid(True)
        plt.legend()
        plt.show()
        
    print(f"Sweep finished. Measured {len(voltages)} points.")
    return voltages, currents

def main():
    # --- Open all instrument resources ---
    instrument1 = open_resource(yokoid8)  # This will be Vx (swept)
    instrument2 = open_resource(yokoid1)  # This will be Vn (fixed)
    instrument3 = open_resource(yokoid2) 
    instrument4 = open_resource(yokoid7) 
    instrument5 = open_resource(yokoid4) 
    instrument6 = open_resource(yokoid5) 
    instrument7 = open_resource(yokoid6) 
    instrument8 = open_resource(yokoid10) 
    rf_source = open_resource(E4432B_address)
    dmm = open_resource(dmmid)

    # --- Define Measurement Parameters ---
    
    # Voltages for Vx Sweep (instrument1)
    start_vx, step_size1, delay1 = -0.2, 0.01, 0.2
    target_vx, step_size_vx = -0.60, 0.002
    
    # Fixed voltages for other instruments
    fixed_vn = -0.3  # Vn (instrument2) will be fixed at this value
    start_voltage3, start_voltage4 = 0.2, -0.0
    start_voltage5, start_voltage6, start_voltage7 = -0.5, -0.5, -0.5
    start_voltage8 = 0.0
    
    # RF Power (fixed during the experiment)
    rf_power = 0  # in dBm
    
    # --- MODIFIED: Frequency Sweep Parameters ---
    start_freq = 80e6  # 80 MHz
    end_freq = 90e6    # 90 MHz
    freq_step = 2e6    # 2 MHz step
    
    # --- Initial wind-up of all instruments to starting conditions ---
    print("--- Setting initial DC voltages and RF power ---")
    windup_voltage(instrument1, start_vx, step_size1, delay1)
    windup_voltage(instrument2, fixed_vn, 0.05, 0.2) # Set Vn to its fixed value
    windup_voltage(instrument3, start_voltage3, 0.05, 0.05)
    windup_voltage(instrument4, start_voltage4, 0.05, 0.05)
    windup_voltage(instrument5, start_voltage5, 0.05, 0.05)
    windup_voltage(instrument6, start_voltage6, 0.05, 0.05)
    windup_voltage(instrument7, start_voltage7, 0.05, 0.05)
    windup_voltage(instrument8, start_voltage8, 0.05, 0.05)
    windup_Prf(rf_source, rf_power, 0.5, 0.2)
    
    # --- Main Loop: Iterate through frequencies ---
    freq_values = np.arange(start_freq, end_freq + freq_step, freq_step)
    all_results = []
    
    print(f"\n--- Starting Experiment: Sweeping Vx from {start_vx}V to {target_vx}V ---")
    print(f"Frequency will be swept from {start_freq/1e6} MHz to {end_freq/1e6} MHz.\n")
    
    for freq in freq_values:
        print(f"--- Setting frequency to {freq/1e6:.2f} MHz ---")
        windup_freq(rf_source, freq, 1e6, 0.2) # Ramp to the target frequency
        
        print(f"--- Now sweeping Vx at this frequency... ---")
        voltages, currents = sweep_V1(instrument1, dmm, start_vx, target_vx, step_size_vx, delay1)
        
        # Reset Vx to its start voltage before the next frequency step
        windup_voltage(instrument1, start_vx, step_size1, delay1)
        
        all_results.append((freq, voltages, currents))

    # --- Save data to file ---
    fname = f'I-Vx-vs-Freq_{int(rf_power)}dBm_{time.strftime("%y%m%d-%H%M")}.txt'
    print(f"\n--- Saving data to {fname} ---")
    lines_to_append = ["# Frequency (Hz), Voltage (V), Current (A)"]
    for freq, voltages, currents in all_results:
        for v, i in zip(voltages, currents):
            line = f"{freq:.6e},{v:.6f},{i:.9e}" # Using scientific notation and CSV format
            lines_to_append.append(line)
    append_multiple_lines(fname, lines_to_append)
    
    # --- Plot final results and save the figure ---
    fig_filename = fname.replace('.txt', '.png')
    print(f"--- Plotting final results and saving to {fig_filename} ---")
    
    plt.figure(figsize=(12, 8))
    if all_results:
        for freq, voltages, currents in all_results:
            label_text = f'Freq = {freq/1e6:.1f} MHz'
            plt.plot(voltages, currents, '-o', label=label_text, markersize=4)
        
        plt.title(f"Current vs. Vx at Various Frequencies (RF Power: {rf_power} dBm)")
        plt.xlabel("V_x (V)")
        plt.ylabel("Current (10nA)")
        plt.legend()
        plt.grid(True)
        
        # Save the figure with high resolution
        plt.savefig(fig_filename, dpi=300)
        
        # Display the figure
        plt.show()
    else:
        print("No data was collected to plot.")
    
    # --- Final status check ---
    print("\n--- Final Instrument Status ---")
    voltage_vx = present_voltage(instrument1)
    print(f"Final Vx: {voltage_vx:.6f} V")
    voltage_vn = present_voltage(instrument2)
    print(f"Final (fixed) Vn: {voltage_vn:.6f} V")
    final_freq = present_freq(rf_source)
    print(f"Final frequency: {final_freq/1e6:.6f} MHz")
    final_power = present_Prf(rf_source)
    print(f"Final power: {final_power:.3f} dBm")

if __name__ == "__main__":
    main()