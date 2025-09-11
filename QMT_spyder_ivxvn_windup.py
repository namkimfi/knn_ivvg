# -*- coding: utf-8 -*-
"""
Created on Sat Oct 19 21:16:20 2024

@author: Admin
"""

# -*- coding: utf-8 -*-
"""
Created on Sat Oct 19 20:38:19 2024

@author: Admin
"""

#!/usr/bin/env python
# coding: utf-8

# In[ ]:


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


# Function to open resource
def open_resource(resource_id):
    rm = pyvisa.ResourceManager()
    return rm.open_resource(resource_id)


# In[ ]:


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


# In[ ]:


# Function to read present voltage
def present_voltage(instrument):
    response = instrument.query("OD")
    match = re.search(r'([+-]?\d+\.\d+E[+-]\d+)', response)
    if match:
        return float(match.group(1))
    else:
        raise ValueError(f"Unexpected response format: {response}")
 


# In[ ]:


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


# In[ ]:


#modified from the original to save data

def sweep_V1(instrument, start_voltage, target_voltage, step_size, delay):
    present_voltage_val = start_voltage
    currents, voltages = [], []
    step_size = abs(step_size) if present_voltage_val < target_voltage else -abs(step_size)
    while abs(present_voltage_val - target_voltage) > abs(step_size) / 2:
        new_voltage = present_voltage_val + step_size
        new_voltage = target_voltage if (step_size > 0 and new_voltage > target_voltage) or (step_size < 0 and new_voltage < target_voltage) else new_voltage
        instrument.write(f"S{new_voltage:.6f}E")
        print(f"Sweeping voltage to: {new_voltage:.6f} V")
        time.sleep(delay)
        present_voltage_val = present_voltage(instrument)
        voltages.append(present_voltage_val)
        dmm = open_resource(dmmid)
        #current = float(dmm.query("READ?"))
        current = float(dmm.query("fetch?"))
        currents.append(current)
       
        
        print(f"Multimeter: {current:.6f} A")
        plt.figure(figsize=(10, 6))
        plt.plot(voltages, currents, 'b-o', label='Current vs Voltage')  # Added label
        plt.title("Current vs Voltage")
        plt.xlabel("Voltage (V)")
        plt.ylabel("Current (10nA)")
        plt.legend()  # Now this will work without warning
        plt.grid(True)
        plt.show()
        plt.close()
        clear_output(wait=True)
        time.sleep(0.2)
    return voltages, currents

def sweep_V2(instrument, start_voltage, target_voltage, step_size, delay):
    present_voltage_val = start_voltage
    step_size = abs(step_size) if present_voltage_val < target_voltage else -abs(step_size)
    while abs(present_voltage_val - target_voltage) > abs(step_size) / 2:
        new_voltage = present_voltage_val + step_size
        new_voltage = target_voltage if (step_size > 0 and new_voltage > target_voltage) or (step_size < 0 and new_voltage < target_voltage) else new_voltage
        instrument.write(f"S{new_voltage:.6f}E")
        print(f"Setting V2 to: {new_voltage:.6f} V")
        time.sleep(delay)
        present_voltage_val = present_voltage(instrument)

    
def sweep_V1_for_fixed_V2(instrument1, instrument2, V1_start, V1_end, V1_step, V2_value, delay):
    sweep_V2(instrument2, present_voltage(instrument2), V2_value, V1_step, delay)
    print(f"V2 fixed at: {V2_value:.6f} V")
    return sweep_V1(instrument1, V1_start, V1_end, V1_step, delay)


# In[7]:

# In[7]:


#double loop confirmed ;Claude created
#append_multiple_lines called to save

def main():
    instrument1 = open_resource(yokoid8) 
    instrument2 = open_resource(yokoid1) 
    instrument3 = open_resource(yokoid2) 
    instrument4 = open_resource(yokoid7) 
    instrument5 = open_resource(yokoid4) 
    instrument6 = open_resource(yokoid5) 
    instrument7 = open_resource(yokoid6) 
    instrument8 = open_resource(yokoid10) 

    start_voltage1, step_size1, delay1 = 0.5, 0.05, 0.2 #ENT
    start_voltage2, step_size2, delay2 = 0.5, 0.05, 0.2 #TR
    start_voltage3, step_size3, delay3 = -0.0, 0.05, 0.05 #Vsd
    start_voltage4, step_size4, delay4 = -0.0, 0.05, 0.05 #pl
    start_voltage5, step_size5, delay5 = -0.5, 0.05, 0.05 #ext
    start_voltage6, step_size6, delay6 = -0.5, 0.05, 0.05 #ext
    start_voltage7, step_size7, delay7 = -0.5, 0.05, 0.05 #ext
    start_voltage8, step_size8, delay8 = -1.0, 0.05, 0.05 #ext

    target_voltage1, step_size0, delay0 = -0.5, 0.01, 0.2  #ENT
    target_voltage2, step_size02, delay02 = -0.5, -0.1, 0.2 #TR
    
    windup_voltage(instrument1, start_voltage1, step_size1, delay1) #ENT
    windup_voltage(instrument2, start_voltage2, step_size2, delay2) #TR
    windup_voltage(instrument3, start_voltage3, step_size3, delay3) #TR
    windup_voltage(instrument4, start_voltage4, step_size4, delay4) #trench
    windup_voltage(instrument5, start_voltage5, step_size5, delay5) #pl
    windup_voltage(instrument6, start_voltage6, step_size6, delay6) #EXT
    windup_voltage(instrument7, start_voltage7, step_size7, delay7) #TR
    windup_voltage(instrument8, start_voltage8, step_size8, delay8) #TR
  
    
    voltage1 = present_voltage(instrument1)
    voltage2 = present_voltage(instrument2)
    print(f"Starter voltage1: {voltage1:.6f} V")
    print(f"Starter voltage2: {voltage2:.6f} V")
    
   
    V2_values = np.arange(start_voltage2, target_voltage2, step_size02)  # Fixed: removed negative sign
    print(f"V2_values to sweep: {V2_values}")  # Debug print


    all_results = []
    print(all_results )

 
        
    for V2 in V2_values:
        print(f"\nSweeping V1 with V2 fixed at {V2:.2f} V")
        voltages, currents = sweep_V1_for_fixed_V2(instrument1, instrument2, start_voltage1, target_voltage1, step_size0, V2, delay1)
        windup_voltage(instrument1, start_voltage1, step_size1, delay1)
        all_results.append((V2, voltages, currents))

    # Save data to file
    fname = 'I-Vx-Vn_p0x5mVxVp_m1mVs_MUXon_2509111421.txt'
    lines_to_append = []
    for V2, voltages, currents in all_results:
        for v, i in zip(voltages, currents):
            line = f"{V2:.6f} {v:.6f} {i:.6f}"
            lines_to_append.append(line)
    append_multiple_lines(fname, lines_to_append)
    
    # Plot all results
    plt.figure(figsize=(12, 8))
    if all_results:  # Check if all_results is not empty
        for V2, voltages, currents in all_results:
            plt.plot(voltages, currents, '-o', label=f'V2 = {V2:.2f} V')
        plt.legend()
    else:
        print("No data to plot - all_results is empty")
        plt.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=plt.gca().transAxes)
    
    plt.title("I vs V_gate with Vs=0 mV")
    plt.xlabel("Vx (V)")
    plt.ylabel("Current (10 nA)")
    plt.grid(True)
    plt.show()
    
    voltage_target = present_voltage(instrument1)
    print(f"Target voltage: {voltage_target:.6f} V")
    dmm = open_resource(dmmid)
    #current = float(dmm.query("READ?"))
    current = float(dmm.query("fetch?"))
    print(f"Multimeter: {current:.6f} A")
    voltage2 = present_voltage(instrument2)
    print(f"Starter voltage2: {voltage2:.6f} V")

if __name__ == "__main__":
    main()



