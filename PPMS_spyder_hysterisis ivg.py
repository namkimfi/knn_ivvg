#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jul  5 14:45:34 2025

@author: namkim
"""

# -*- coding: utf-8 -*-
"""
Hysteresis Loop Measurement Code
Modified from PPMS_spyder_ivvg_windup_v3.py
Created for hysteresis characterization of devices

@author: Modified by Claude
"""

import pyvisa
import time
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import clear_output
import re
from datetime import datetime

# GPIB addresses
yokoid1 = "GPIB1::4::INSTR"  #x
yokoid2 = "GPIB1::5::INSTR" #pl
yokoid3 = "GPIB1::6::INSTR" #ent
yokoid4 = "GPIB1::9::INSTR" #tr
yokoid5 = "GPIB1::3::INSTR"  #sd
dmmid = "GPIB1::22::INSTR"

def open_resource(resource_id):
    rm = pyvisa.ResourceManager()
    return rm.open_resource(resource_id)

def append_new_line(file_name, text_to_append):
    with open(file_name, "a+") as file_object:
        file_object.seek(0)
        data = file_object.read(100)
        if len(data) > 0:
            file_object.write("\n")
        file_object.write(text_to_append)

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

def present_voltage(instrument):
    response = instrument.query("OD")
    match = re.search(r'([+-]?\d+\.\d+E[+-]\d+)', response)
    if match:
        return float(match.group(1))
    else:
        raise ValueError(f"Unexpected response format: {response}")

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

def sweep_V1_hysteresis(instrument, start_voltage, target_voltage, step_size, delay, direction="forward"):
    """
    Sweep voltage in specified direction for hysteresis measurement
    direction: "forward" (start to target) or "backward" (target to start)
    """
    present_voltage_val = start_voltage
    currents, voltages = [], []
    
    if direction == "forward":
        step_size = abs(step_size) if start_voltage < target_voltage else -abs(step_size)
        end_voltage = target_voltage
    else:  # backward
        step_size = abs(step_size) if start_voltage > target_voltage else -abs(step_size)
        end_voltage = target_voltage
    
    print(f"Starting {direction} sweep from {start_voltage:.3f}V to {end_voltage:.3f}V")
    
    while abs(present_voltage_val - end_voltage) > abs(step_size) / 2:
        new_voltage = present_voltage_val + step_size
        # Ensure we don't overshoot the target
        if (step_size > 0 and new_voltage > end_voltage) or (step_size < 0 and new_voltage < end_voltage):
            new_voltage = end_voltage
        
        instrument.write(f"S{new_voltage:.6f}E")
        print(f"{direction.capitalize()} sweep - voltage: {new_voltage:.6f} V")
        time.sleep(delay)
        
        # Read actual voltage and current
        present_voltage_val = present_voltage(instrument)
        voltages.append(present_voltage_val)
        
        dmm = open_resource(dmmid)
        current = float(dmm.query("READ?"))
        currents.append(current)
        dmm.close()
        
        print(f"Measured: V={present_voltage_val:.6f}V, I={current:.6e}A")
        
    # Ensure we reach the exact target voltage
    instrument.write(f"S{end_voltage:.6f}E")
    time.sleep(delay)
    present_voltage_val = present_voltage(instrument)
    voltages.append(present_voltage_val)
    
    dmm = open_resource(dmmid)
    current = float(dmm.query("READ?"))
    currents.append(current)
    dmm.close()
    
    return voltages, currents

def perform_hysteresis_loop(instrument1, instrument2, V_min, V_max, step_size, delay, V2_fixed=0.0, num_cycles=1):
    """
    Perform complete hysteresis loop measurement
    
    Parameters:
    - V_min: minimum voltage of the sweep
    - V_max: maximum voltage of the sweep  
    - step_size: voltage step size
    - delay: delay between measurements
    - V2_fixed: fixed voltage for second instrument
    - num_cycles: number of complete hysteresis cycles
    """
    
    all_hysteresis_data = []
    
    # Set V2 to fixed value
    windup_voltage(instrument2, V2_fixed, abs(step_size), delay)
    print(f"V2 fixed at: {V2_fixed:.6f} V")
    
    for cycle in range(num_cycles):
        print(f"\n=== HYSTERESIS CYCLE {cycle + 1}/{num_cycles} ===")
        
        # Start from V_min
        windup_voltage(instrument1, V_min, abs(step_size), delay)
        
        # Forward sweep: V_min → V_max
        print(f"\nForward sweep {cycle + 1}: {V_min:.3f}V → {V_max:.3f}V")
        voltages_forward, currents_forward = sweep_V1_hysteresis(
            instrument1, V_min, V_max, step_size, delay, "forward"
        )
        
        # Backward sweep: V_max → V_min
        print(f"\nBackward sweep {cycle + 1}: {V_max:.3f}V → {V_min:.3f}V")
        voltages_backward, currents_backward = sweep_V1_hysteresis(
            instrument1, V_max, V_min, -step_size, delay, "backward"
        )
        
        # Store data for this cycle
        cycle_data = {
            'cycle': cycle + 1,
            'V2_fixed': V2_fixed,
            'forward': {
                'voltages': voltages_forward,
                'currents': currents_forward
            },
            'backward': {
                'voltages': voltages_backward,
                'currents': currents_backward
            }
        }
        all_hysteresis_data.append(cycle_data)
        
        # Plot real-time hysteresis loop for this cycle
        plot_hysteresis_cycle(cycle_data, cycle + 1)
        
    return all_hysteresis_data

def plot_hysteresis_cycle(cycle_data, cycle_num):
    """Plot hysteresis loop for a single cycle"""
    plt.figure(figsize=(10, 8))
    
    # Plot forward sweep
    plt.plot(cycle_data['forward']['voltages'], cycle_data['forward']['currents'], 
             'b-o', markersize=3, label='Forward sweep', linewidth=1.5)
    
    # Plot backward sweep
    plt.plot(cycle_data['backward']['voltages'], cycle_data['backward']['currents'], 
             'r-s', markersize=3, label='Backward sweep', linewidth=1.5)
    
    plt.title(f"Hysteresis Loop - Cycle {cycle_num}\nV2 = {cycle_data['V2_fixed']:.3f} V")
    plt.xlabel("Voltage V1 (V)")
    plt.ylabel("Current (A)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Add arrows to show sweep direction
    plt.annotate('Forward', xy=(0.02, 0.95), xycoords='axes fraction', 
                color='blue', fontweight='bold')
    plt.annotate('Backward', xy=(0.02, 0.90), xycoords='axes fraction', 
                color='red', fontweight='bold')
    
    plt.tight_layout()
    plt.show()
    
def plot_all_hysteresis_cycles(all_data):
    """Plot all hysteresis cycles together"""
    plt.figure(figsize=(12, 10))
    
    colors_forward = plt.cm.Blues(np.linspace(0.4, 1.0, len(all_data)))
    colors_backward = plt.cm.Reds(np.linspace(0.4, 1.0, len(all_data)))
    
    for i, cycle_data in enumerate(all_data):
        cycle_num = cycle_data['cycle']
        
        plt.plot(cycle_data['forward']['voltages'], cycle_data['forward']['currents'], 
                '-o', color=colors_forward[i], markersize=2, 
                label=f'Cycle {cycle_num} Forward', linewidth=1.5)
        
        plt.plot(cycle_data['backward']['voltages'], cycle_data['backward']['currents'], 
                '-s', color=colors_backward[i], markersize=2, 
                label=f'Cycle {cycle_num} Backward', linewidth=1.5)
    
    plt.title(f"All Hysteresis Cycles\nV2 = {all_data[0]['V2_fixed']:.3f} V")
    plt.xlabel("Voltage V1 (V)")
    plt.ylabel("Current (A)")
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

def analyze_hysteresis(all_data):
    """Analyze hysteresis characteristics"""
    print("\n=== HYSTERESIS ANALYSIS ===")
    
    for cycle_data in all_data:
        cycle_num = cycle_data['cycle']
        forward_v = np.array(cycle_data['forward']['voltages'])
        forward_i = np.array(cycle_data['forward']['currents'])
        backward_v = np.array(cycle_data['backward']['voltages'])
        backward_i = np.array(cycle_data['backward']['currents'])
        
        # Find common voltage range for comparison
        v_min_common = max(min(forward_v), min(backward_v))
        v_max_common = min(max(forward_v), max(backward_v))
        
        if v_max_common > v_min_common:
            # Interpolate currents at common voltages
            v_common = np.linspace(v_min_common, v_max_common, 50)
            i_forward_interp = np.interp(v_common, forward_v, forward_i)
            i_backward_interp = np.interp(v_common, backward_v, backward_i)
            
            # Calculate hysteresis metrics
            max_hysteresis = np.max(np.abs(i_forward_interp - i_backward_interp))
            avg_hysteresis = np.mean(np.abs(i_forward_interp - i_backward_interp))
            
            print(f"\nCycle {cycle_num}:")
            print(f"  Voltage range analyzed: {v_min_common:.3f} to {v_max_common:.3f} V")
            print(f"  Maximum hysteresis: {max_hysteresis:.2e} A")
            print(f"  Average hysteresis: {avg_hysteresis:.2e} A")
            print(f"  Forward current range: {min(forward_i):.2e} to {max(forward_i):.2e} A")
            print(f"  Backward current range: {min(backward_i):.2e} to {max(backward_i):.2e} A")

def save_hysteresis_data(all_data, filename_prefix="hysteresis"):
    """Save hysteresis data to files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for cycle_data in all_data:
        cycle_num = cycle_data['cycle']
        V2_fixed = cycle_data['V2_fixed']
        
        # Save data file
        fname = f"{filename_prefix}_cycle_{cycle_num}_{timestamp}.txt"
        lines_to_append = []
        
        # Header
        lines_to_append.append(f"# Hysteresis measurement - Cycle {cycle_num}")
        lines_to_append.append(f"# V2_fixed = {V2_fixed:.6f} V")
        lines_to_append.append(f"# Columns: Sweep_Direction V1(V) I(A)")
        
        # Forward sweep data
        for v, i in zip(cycle_data['forward']['voltages'], cycle_data['forward']['currents']):
            lines_to_append.append(f"Forward {v:.6f} {i:.6e}")
        
        # Backward sweep data
        for v, i in zip(cycle_data['backward']['voltages'], cycle_data['backward']['currents']):
            lines_to_append.append(f"Backward {v:.6f} {i:.6e}")
        
        append_multiple_lines(fname, lines_to_append)
        print(f"Data saved to: {fname}")

def main_hysteresis():
    """Main function for hysteresis measurement"""
    
    # Open instruments
    instrument1 = open_resource(yokoid1)  # Sweep voltage
    instrument2 = open_resource(yokoid4)  # Fixed voltage
    instrument3 = open_resource(yokoid2)  # Additional channels
    instrument4 = open_resource(yokoid3)
    instrument5 = open_resource(yokoid5)
    
    # Initialize all instruments to 0V
    init_voltage = 0.0
    step_init = 0.05
    delay_init = 0.1
    
    print("Initializing all instruments...")
    windup_voltage(instrument1, init_voltage, step_init, delay_init)
    windup_voltage(instrument2, init_voltage, step_init, delay_init)
    windup_voltage(instrument3, init_voltage, step_init, delay_init)
    windup_voltage(instrument4, init_voltage, step_init, delay_init)
    windup_voltage(instrument5, init_voltage, step_init, delay_init)
    
    # Hysteresis measurement parameters
    V_min = -0.6          # Minimum voltage
    V_max = -2.0          # Maximum voltage
    step_size = 0.02      # Voltage step size
    delay = 0.2           # Delay between measurements
    V2_fixed = 0.0        # Fixed voltage for instrument2
    num_cycles = 2        # Number of hysteresis cycles
    
    print(f"\n=== HYSTERESIS MEASUREMENT PARAMETERS ===")
    print(f"Voltage range: {V_min} V to {V_max} V")
    print(f"Step size: {step_size} V")
    print(f"Delay: {delay} s")
    print(f"Fixed V2: {V2_fixed} V")
    print(f"Number of cycles: {num_cycles}")
    
    # Perform hysteresis measurement
    all_hysteresis_data = perform_hysteresis_loop(
        instrument1, instrument2, V_min, V_max, step_size, delay, V2_fixed, num_cycles
    )
    
    # Plot all cycles together
    plot_all_hysteresis_cycles(all_hysteresis_data)
    
    # Analyze hysteresis
    analyze_hysteresis(all_hysteresis_data)
    
    # Save data
    save_hysteresis_data(all_hysteresis_data)
    
    # Return instruments to initial state
    print("\nReturning instruments to initial state...")
    windup_voltage(instrument1, init_voltage, step_init, delay_init)
    windup_voltage(instrument2, init_voltage, step_init, delay_init)
    
    print("\nHysteresis measurement completed!")
    
    # Close instruments
    instrument1.close()
    instrument2.close()
    instrument3.close()
    instrument4.close()
    instrument5.close()

if __name__ == "__main__":
    main_hysteresis()