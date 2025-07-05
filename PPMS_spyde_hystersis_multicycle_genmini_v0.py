# -*- coding: utf-8 -*-
"""
Created on Sat Jul  5 18:00:27 2025

@author: ADMIN
"""

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
@version: 2.0 - Corrected data saving, added plot saving, and refined multi-cycle capabilities.
"""

import pyvisa
import time
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import clear_output
import re
from datetime import datetime
import os

# --- GPIB addresses ---
yokoid1 = "GPIB1::4::INSTR"  # Voltage source for sweep (V1)
yokoid2 = "GPIB1::5::INSTR"  # Additional instrument
yokoid3 = "GPIB1::6::INSTR"  # Additional instrument
yokoid4 = "GPIB1::9::INSTR"  # Voltage source for fixed voltage (V2)
yokoid5 = "GPIB1::3::INSTR"  # Additional instrument
dmmid = "GPIB1::22::INSTR"   # Digital Multimeter for current measurement

def open_resource(resource_id):
    """Opens a connection to a GPIB instrument."""
    rm = pyvisa.ResourceManager()
    return rm.open_resource(resource_id)

def append_multiple_lines(file_name, lines_to_append):
    """Appends multiple lines of text to a file, creating it if it doesn't exist."""
    with open(file_name, "a") as file_object:
        for line in lines_to_append:
            file_object.write(line + "\n")

def present_voltage(instrument):
    """Queries the instrument and returns the present output voltage."""
    try:
        response = instrument.query("OD")
        match = re.search(r'([+-]?\d+\.\d+E[+-]\d+)', response)
        if match:
            return float(match.group(1))
        else:
            # Fallback for non-scientific notation responses
            numeric_part = re.search(r'([+-]?\d+\.\d+)', response)
            if numeric_part:
                return float(numeric_part.group(1))
            raise ValueError(f"Unexpected response format from instrument: {response}")
    except pyvisa.errors.VisaIOError as e:
        print(f"Error communicating with instrument: {e}")
        return 0.0 # Return a default value in case of communication error

def windup_voltage(instrument, target_voltage, step_size, delay):
    """Gradually changes the voltage of an instrument to a target value."""
    present_voltage_val = present_voltage(instrument)
    step_size = abs(step_size) if present_voltage_val < target_voltage else -abs(step_size)

    while abs(present_voltage_val - target_voltage) > abs(step_size) / 2:
        new_voltage = present_voltage_val + step_size
        if (step_size > 0 and new_voltage > target_voltage) or \
           (step_size < 0 and new_voltage < target_voltage):
            new_voltage = target_voltage
        
        instrument.write(f"S{new_voltage:.6f}E")
        print(f"Winding up voltage to: {new_voltage:.6f} V")
        time.sleep(delay)
        present_voltage_val = present_voltage(instrument)

    instrument.write(f"S{target_voltage:.6f}E")
    print(f"Final voltage set to: {target_voltage:.6f} V")

def sweep_V1_hysteresis(instrument, start_voltage, target_voltage, step_size, delay, dmm, direction="forward"):
    """
    Sweeps the voltage from a start to a target value for hysteresis measurement.
    
    Args:
        instrument: The voltage source instrument to sweep.
        start_voltage (float): The starting voltage.
        target_voltage (float): The ending voltage.
        step_size (float): The voltage increment.
        delay (float): The time to wait between steps.
        dmm: The digital multimeter instrument for reading current.
        direction (str): "forward" or "backward".
    """
    voltages, currents = [], []
    
    num_steps = int(abs(target_voltage - start_voltage) / abs(step_size))
    voltage_steps = np.linspace(start_voltage, target_voltage, num_steps + 1)
    
    print(f"Starting {direction} sweep from {start_voltage:.3f}V to {target_voltage:.3f}V")
    
    for v_setpoint in voltage_steps:
        instrument.write(f"S{v_setpoint:.6f}E")
        time.sleep(delay)
        
        # Read the actual voltage and current
        actual_voltage = present_voltage(instrument)
        voltages.append(actual_voltage)
        
        current_str = dmm.query("READ?")
        current = float(current_str)
        currents.append(current)
        
        print(f"  {direction.capitalize()} sweep - Set: {v_setpoint:.6f}V, Measured: V={actual_voltage:.6f}V, I={current:.6e}A")
        clear_output(wait=True)

    return voltages, currents

def perform_hysteresis_loop(instrument1, instrument2, dmm, V_min, V_max, step_size, delay, V2_fixed=0.0, num_cycles=1, results_dir="results"):
    """
    Performs a complete multi-cycle hysteresis loop measurement.
    """
    all_hysteresis_data = []
    
    # Set the fixed voltage on the second instrument
    print(f"Setting fixed voltage on instrument 2 to {V2_fixed:.6f} V...")
    windup_voltage(instrument2, V2_fixed, abs(step_size) * 2, delay)
    print(f"V2 fixed at: {V2_fixed:.6f} V")
    
    for cycle in range(num_cycles):
        print(f"\n{'='*15} HYSTERESIS CYCLE {cycle + 1}/{num_cycles} {'='*15}")
        
        # Start at V_min
        windup_voltage(instrument1, V_min, abs(step_size) * 2, delay)
        
        # Forward sweep: V_min → V_max
        voltages_forward, currents_forward = sweep_V1_hysteresis(
            instrument1, V_min, V_max, step_size, delay, dmm, "forward"
        )
        
        # Backward sweep: V_max → V_min
        voltages_backward, currents_backward = sweep_V1_hysteresis(
            instrument1, V_max, V_min, -step_size, delay, dmm, "backward"
        )
        
        cycle_data = {
            'cycle': cycle + 1,
            'V2_fixed': V2_fixed,
            'forward': {'voltages': voltages_forward, 'currents': currents_forward},
            'backward': {'voltages': voltages_backward, 'currents': currents_backward}
        }
        all_hysteresis_data.append(cycle_data)
        
        # Plot and save the loop for the current cycle
        plot_hysteresis_cycle(cycle_data, cycle + 1, results_dir)
        
    return all_hysteresis_data

def plot_hysteresis_cycle(cycle_data, cycle_num, results_dir, timestamp=""):
    """Plots and saves the hysteresis loop for a single cycle."""
    if not timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    plt.figure(figsize=(10, 8))
    
    plt.plot(cycle_data['forward']['voltages'], cycle_data['forward']['currents'], 
             'b-o', markersize=4, label='Forward Sweep', linewidth=1.5)
    
    plt.plot(cycle_data['backward']['voltages'], cycle_data['backward']['currents'], 
             'r-s', markersize=4, label='Backward Sweep', linewidth=1.5)
    
    plt.title(f"Hysteresis Loop - Cycle {cycle_num}\n(V2 = {cycle_data['V2_fixed']:.3f} V)")
    plt.xlabel("Voltage V1 (V)")
    plt.ylabel("Current (A)")
    plt.legend()
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    
    plt.tight_layout()
    
    # Save the plot
    plot_filename = os.path.join(results_dir, f"Hysteresis_Plot_Cycle_{cycle_num}_{timestamp}.png")
    plt.savefig(plot_filename, dpi=300)
    print(f"Plot saved to: {plot_filename}")
    plt.show()

def plot_all_hysteresis_cycles(all_data, results_dir, timestamp=""):
    """Plots and saves all hysteresis cycles on a single graph."""
    if not timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    plt.figure(figsize=(12, 10))
    
    num_cycles = len(all_data)
    colors_forward = plt.cm.Blues(np.linspace(0.5, 1.0, num_cycles))
    colors_backward = plt.cm.Reds(np.linspace(0.5, 1.0, num_cycles))
    
    for i, cycle_data in enumerate(all_data):
        cycle_num = cycle_data['cycle']
        
        plt.plot(cycle_data['forward']['voltages'], cycle_data['forward']['currents'], 
                 '-o', color=colors_forward[i], markersize=3, 
                 label=f'Cycle {cycle_num} Forward', linewidth=1.5)
        
        plt.plot(cycle_data['backward']['voltages'], cycle_data['backward']['currents'], 
                 '-s', color=colors_backward[i], markersize=3, 
                 label=f'Cycle {cycle_num} Backward', linewidth=1.5)
    
    plt.title(f"All Hysteresis Cycles (Total: {num_cycles})\n(V2 = {all_data[0]['V2_fixed']:.3f} V)")
    plt.xlabel("Voltage V1 (V)")
    plt.ylabel("Current (A)")
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.tight_layout()
    
    # Save the plot
    plot_filename = os.path.join(results_dir, f"Hysteresis_Plot_All_Cycles_{timestamp}.png")
    plt.savefig(plot_filename, dpi=300)
    print(f"Summary plot saved to: {plot_filename}")
    plt.show()

def save_hysteresis_data(all_data, results_dir, filename_prefix="hysteresis"):
    """Saves all hysteresis data to a single, well-formatted text file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = os.path.join(results_dir, f"{filename_prefix}_data_{timestamp}.txt")
    
    lines_to_append = []
    
    # --- Main Header ---
    lines_to_append.append(f"# Hysteresis Measurement Data")
    lines_to_append.append(f"# Date and Time: {timestamp}")
    lines_to_append.append(f"# Fixed Voltage (V2): {all_data[0]['V2_fixed']:.6f} V")
    lines_to_append.append("# ----------------------------------------")
    
    for cycle_data in all_data:
        cycle_num = cycle_data['cycle']
        
        # --- Cycle Header ---
        lines_to_append.append(f"\n# === Cycle {cycle_num} ===")
        lines_to_append.append(f"# Columns: Sweep_Direction, V1(V), I(A)")
        
        # Forward sweep data
        for v, i in zip(cycle_data['forward']['voltages'], cycle_data['forward']['currents']):
            lines_to_append.append(f"Forward, {v:.6f}, {i:.6e}")
        
        # Backward sweep data
        for v, i in zip(cycle_data['backward']['voltages'], cycle_data['backward']['currents']):
            lines_to_append.append(f"Backward, {v:.6f}, {i:.6e}")
            
    append_multiple_lines(fname, lines_to_append)
    print(f"All data successfully saved to: {fname}")

def main_hysteresis():
    """Main function to run the hysteresis measurement experiment."""
    
    # --- Create a directory for results ---
    results_dir = "hysteresis_results"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    
    try:
        # --- Open Instruments ---
        instrument1 = open_resource(yokoid1)  # Sweep voltage
        instrument2 = open_resource(yokoid4)  # Fixed voltage
        instrument3 = open_resource(yokoid2)
        instrument4 = open_resource(yokoid3)
        instrument5 = open_resource(yokoid5)
        dmm = open_resource(dmmid)
        
        all_instruments = [instrument1, instrument2, instrument3, instrument4, instrument5]
        
        # --- Initialize all instruments to 0V ---
        print("Initializing all instruments to 0V...")
        for inst in all_instruments:
            windup_voltage(inst, 0.0, 0.05, 0.1)
        
        # --- Hysteresis Measurement Parameters ---
        V_min = -1.6         # Minimum voltage
        V_max = -0.6           # Maximum voltage
        step_size = 0.1       # Voltage step size
        delay = 0.2           # Delay between measurements (in seconds)
        V2_fixed = 0.0        # Fixed voltage for the second instrument
        num_cycles = 2        # Number of hysteresis cycles to perform
        
        print("\n" + "="*40)
        print("      HYSTERESIS MEASUREMENT PARAMETERS")
        print("="*40)
        print(f"  Voltage Range (V1): {V_min} V to {V_max} V")
        print(f"  Step Size:          {step_size} V")
        print(f"  Delay:              {delay} s")
        print(f"  Fixed Voltage (V2): {V2_fixed} V")
        print(f"  Number of Cycles:   {num_cycles}")
        print("="*40 + "\n")
        
        # --- Perform Hysteresis Measurement ---
        all_hysteresis_data = perform_hysteresis_loop(
            instrument1, instrument2, dmm, V_min, V_max, step_size, delay, V2_fixed, num_cycles, results_dir
        )
        
        # --- Plot all cycles together ---
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plot_all_hysteresis_cycles(all_hysteresis_data, results_dir, timestamp)
        
        # --- Save all data ---
        save_hysteresis_data(all_hysteresis_data, results_dir, "hysteresis_measurement")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        # --- Return instruments to 0V and close connections ---
        print("\nReturning instruments to 0V and closing connections...")
        try:
            for inst in all_instruments:
                windup_voltage(inst, 0.0, 0.05, 0.1)
                inst.close()
            dmm.close()
        except NameError:
            print("Could not close instruments as they were not opened.")
        except Exception as e:
            print(f"An error occurred during cleanup: {e}")
            
        print("\nHysteresis measurement completed!")

if __name__ == "__main__":
    main_hysteresis()