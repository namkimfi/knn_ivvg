# -*- coding: utf-8 -*-
"""
Created on Tue Sep 16 12:11:47 2025

@author: SEQD-RFSET
"""
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 11 15:47:24 2025

@author: SEQD-RFSET
"""

#!/usr/bin/env python
# coding: utf-8

# Modified to sweep current vs voltage1 for various frequencies
# Original code by IHLee, modified by Claude

import pyvisa
import time
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import clear_output
import re  # Regular expressions module
from datetime import datetime

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

def set_freq(instrument, target_freq, step_size, delay):
    """Set frequency with gradual stepping"""
    present_freq_val = present_freq(instrument)
    if present_freq_val is None:
        print("Warning: Could not read current frequency, setting directly")
        instrument.write(f'FREQ {target_freq}')
        return
        
    step_size = abs(step_size) if present_freq_val < target_freq else -abs(step_size)
    
    while abs(present_freq_val - target_freq) > abs(step_size) / 2:
        new_freq = present_freq_val + step_size
        new_freq = target_freq if (step_size > 0 and new_freq > target_freq) or (step_size < 0 and new_freq < target_freq) else new_freq
        instrument.write(f'FREQ {new_freq}')
        print(f"Setting freq to: {new_freq:.0f} Hz")
        time.sleep(delay)
        present_freq_val = present_freq(instrument)
        if present_freq_val is None:
            break
    
    instrument.write(f'FREQ {target_freq}')
    print(f"Final freq set to: {target_freq:.0f} Hz")

def windup_freq(instrument, start_voltage, step_size, delay):
    present_voltage_val = present_freq(instrument)
    if present_voltage_val is None:
        instrument.write(f'FREQ {start_voltage}')
        return
        
    step_size = abs(step_size) if present_voltage_val < start_voltage else -abs(step_size)
    while abs(present_voltage_val - start_voltage) > abs(step_size) / 2:
        new_voltage = present_voltage_val + step_size
        new_voltage = start_voltage if (step_size > 0 and new_voltage > start_voltage) or (step_size < 0 and new_voltage < start_voltage) else new_voltage
        instrument.write(f'FREQ {new_voltage}')
        print(f"Wind-up freq to: {new_voltage:.3f} Hz")
        time.sleep(delay)
        present_voltage_val = present_freq(instrument)
        if present_voltage_val is None:
            break
    instrument.write(f'FREQ {start_voltage}')
    print(f"Final freq set to: {start_voltage:.3f} Hz")

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

def windup_Prf(instrument, start_voltage, step_size, delay):
    present_voltage_val = present_Prf(instrument)
    if present_voltage_val is None:
        instrument.write(f'POW {start_voltage}')
        return
        
    step_size = abs(step_size) if present_voltage_val < start_voltage else -abs(step_size)
    while abs(present_voltage_val - start_voltage) > abs(step_size) / 2:
        new_voltage = present_voltage_val + step_size
        new_voltage = start_voltage if (step_size > 0 and new_voltage > start_voltage) or (step_size < 0 and new_voltage < start_voltage) else new_voltage
        instrument.write(f'POW {new_voltage}')
        print(f"Wind-up power to: {new_voltage:.3f} dBm")
        time.sleep(delay)
        present_voltage_val = present_Prf(instrument)
        if present_voltage_val is None:
            break
    instrument.write(f'POW {start_voltage}')
    print(f"Final power set to: {start_voltage:.3f} dBm")

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

# Modified to sweep voltage for fixed frequency
def sweep_V1(instrument, start_voltage, target_voltage, step_size, delay, frequency_label=""):
    present_voltage_val = start_voltage
    currents, voltages = [], []
    step_size = abs(step_size) if present_voltage_val < target_voltage else -abs(step_size)
    
    while abs(present_voltage_val - target_voltage) > abs(step_size) / 2:
        new_voltage = present_voltage_val + step_size
        new_voltage = target_voltage if (step_size > 0 and new_voltage > target_voltage) or (step_size < 0 and new_voltage < target_voltage) else new_voltage
        instrument.write(f"S{new_voltage:.6f}E")
        print(f"Sweeping voltage to: {new_voltage:.6f} V {frequency_label}")
        time.sleep(delay)
        present_voltage_val = present_voltage(instrument)
        voltages.append(present_voltage_val)
        
        dmm = open_resource(dmmid)
        current = float(dmm.query("fetch?"))
        dmm.close()
        currents.append(current)
       
        print(f"Multimeter: {current:.6f} A")
        
        # Real-time plotting
        plt.figure(figsize=(10, 6))
        plt.plot(voltages, currents, 'b-o', label=f'Current vs Voltage {frequency_label}')
        plt.title(f"Current vs Voltage {frequency_label}")
        plt.xlabel("Voltage (V)")
        plt.ylabel("Current (nA)")
        plt.grid(True)
        plt.legend()
        plt.show()
        plt.close()
        clear_output(wait=True)
        time.sleep(0.2)
    
    return voltages, currents

def sweep_V1_for_fixed_freq(instrument1, rf_instrument, V1_start, V1_end, V1_step, frequency, delay):
    """Sweep V1 for a fixed frequency"""
    # Set the frequency
    set_freq(rf_instrument, frequency, 1e6, 0.1)  # 1MHz steps for frequency change
    
    freq_mhz = frequency / 1e6
    frequency_label = f"@ {freq_mhz:.1f} MHz"
    print(f"Frequency fixed at: {frequency:.0f} Hz ({freq_mhz:.1f} MHz)")
    
    # Allow time for frequency to settle
    time.sleep(0.5)
    
    return sweep_V1(instrument1, V1_start, V1_end, V1_step, delay, frequency_label)

def main():
    # Initialize instruments
    instrument1 = open_resource(yokoid8)  # V1 - swept voltage
    instrument2 = open_resource(yokoid1)  # V2 - ENT
    instrument3 = open_resource(yokoid2)  # V3 - pl
    instrument4 = open_resource(yokoid7)  # V4 - pl
    instrument5 = open_resource(yokoid4)  # V5 - mux
    instrument6 = open_resource(yokoid5)  # V6 - mux
    instrument7 = open_resource(yokoid6)  # V7 - mux
    instrument8 = open_resource(yokoid10) # V8 - sd
    instrument = open_resource(E4432B_address)  # RF source
    
    # Voltage settings for all channels (same as original)
    start_voltage1, step_size1, delay1 = -0.2, 0.01, 0.2  # Exit - swept voltage
    start_voltage2, step_size2, delay2 = -0.3, 0.05, 0.2  # ENT
    start_voltage3, step_size3, delay3 = 0.2, 0.05, 0.05  # pl
    start_voltage4, step_size4, delay4 = -0.0, 0.05, 0.05 # pl
    start_voltage5, step_size5, delay5 = -0.5, 0.05, 0.05 # mux
    start_voltage6, step_size6, delay6 = -0.5, 0.05, 0.05 # mux
    start_voltage7, step_size7, delay7 = -0.5, 0.05, 0.05 # mux
    start_voltage8, step_size8, delay8 = 0.0, 0.05, 0.05  # sd
    start_power, step_size_p, delay_p = 0, 0.5, 0.2       # RF power
    
    # Voltage sweep parameters
    target_voltage1, step_size0, delay0 = -0.60, 0.004, 0.2  # Exit voltage sweep
    
    # Set up all fixed voltages
    print("Setting up fixed voltages...")
    windup_voltage(instrument1, start_voltage1, step_size1, delay1)   # Start position for swept voltage
    windup_voltage(instrument2, start_voltage2, step_size2, delay2)   # ENT
    windup_voltage(instrument3, start_voltage3, step_size3, delay3)   # pl
    windup_voltage(instrument4, start_voltage4, step_size4, delay4)   # pl
    windup_voltage(instrument5, start_voltage5, step_size5, delay5)   # mux
    windup_voltage(instrument6, start_voltage6, step_size6, delay6)   # mux
    windup_voltage(instrument7, start_voltage7, step_size7, delay7)   # mux
    windup_voltage(instrument8, start_voltage8, step_size8, delay8)   # sd
    
    # Set up RF power
    windup_Prf(instrument, start_power, step_size_p, delay_p)
    
    # Read initial states
    voltage1 = present_voltage(instrument1)
    voltage2 = present_voltage(instrument2)
    power = present_Prf(instrument)
    
    print(f"Initial Exit voltage: {voltage1:.6f} V")
    print(f"Initial ENT voltage: {voltage2:.6f} V")
    print(f"Initial RF power: {power:.3f} dBm")
   
    # Define frequency values to sweep (in Hz)
    frequencies = np.array([50e6, 60e6, 70e6, 80e6, 90e6])  # 85-93 MHz in 2 MHz steps
    print(f"Frequencies to sweep: {frequencies/1e6} MHz")
    
    all_results = []
    print(f"Initial all_results: {all_results}")
    
    # Loop through frequencies instead of V2 values
    for freq in frequencies:
        freq_mhz = freq / 1e6
        print(f"\n=== Sweeping V1 with frequency fixed at {freq_mhz:.1f} MHz ===")
        
        voltages, currents = sweep_V1_for_fixed_freq(
            instrument1, instrument, start_voltage1, target_voltage1, step_size0, freq, delay0
        )
        
        # Return to start position for next frequency
        windup_voltage(instrument1, start_voltage1, step_size1, delay1)
        
        all_results.append((freq, voltages, currents))
        print(f"Completed sweep at {freq_mhz:.1f} MHz: {len(voltages)} points collected")

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    fname = f'I-Vx-freq_sweep_{timestamp}.txt'
    
    # Save data to file
    print(f"Saving data to {fname}...")
    lines_to_append = []
    lines_to_append.append("# Frequency(Hz) Voltage(V) Current(A)")
    
    for freq, voltages, currents in all_results:
        for v, i in zip(voltages, currents):
            line = f"{freq:.0f} {v:.6f} {i:.6f}"
            lines_to_append.append(line)
    
    append_multiple_lines(fname, lines_to_append)
    print(f"Data saved: {len(lines_to_append)-1} data points")
    
    # Plot all results
    plt.figure(figsize=(12, 8))
    if all_results:
        colors = plt.cm.viridis(np.linspace(0, 1, len(all_results)))
        
        for i, (freq, voltages, currents) in enumerate(all_results):
            freq_mhz = freq / 1e6
            plt.plot(voltages, currents, '-o', 
                    color=colors[i], 
                    label=f'{freq_mhz:.1f} MHz',
                    markersize=4, linewidth=2)
        
        plt.title("Current vs Exit Voltage for Various RF Frequencies")
        plt.xlabel("Exit Voltage (V)")
        plt.ylabel("Current (nA)")
        plt.legend(title="RF Frequency")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Save the plot
        plot_fname = f'I-Vx-freq_sweep_{timestamp}.png'
        plt.savefig(plot_fname, dpi=300, bbox_inches='tight')
        print(f"Plot saved as {plot_fname}")
        
        plt.show()
    else:
        print("No data to plot")
    
    # Final readings
    voltage_target = present_voltage(instrument1)
    dmm = open_resource(dmmid)
    current = float(dmm.query("fetch?"))
    dmm.close()
    
    final_freq = present_freq(instrument)
    final_power = present_Prf(instrument)
    
    print(f"\nFinal states:")
    print(f"Exit voltage: {voltage_target:.6f} V")
    print(f"Current: {current:.6f} A")
    print(f"RF frequency: {final_freq:.0f} Hz ({final_freq/1e6:.1f} MHz)")
    print(f"RF power: {final_power:.3f} dBm")

if __name__ == "__main__":
    main()
