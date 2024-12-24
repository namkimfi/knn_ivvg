##With HP E4432B signal generator, 
#wind-up of frequency & rfpower
#Claude created

# -*- coding: utf-8 -*-
"""
Created on Mon Dec 23 16:01:17 2024

@author: Admin
"""

##With HP E4432B signal generator, 
#wind-up of frequency
#Claude created

import pyvisa
import re
import time

#rm = pyvisa.ResourceManager()
E4432B_address = "GPIB0::13::INSTR"
#instrument = rm.open_resource(E4432B_address)
#start_voltage=0
#step_size=0.02
#delay=0.1
def open_resource(resource_id):
    rm = pyvisa.ResourceManager()
    return rm.open_resource(resource_id)

def present_freq(instrument):
    try:
        response = instrument.query("FREQ?")  # Note the '?' to query the value
        #match = re.search(r'([+-]?\d+\.\d+)', response)
        match = re.search(r'([+-]?\d+\.\d+E[+-]\d+)', response)
        if match:
            return float(match.group(1))
        else:
            raise ValueError(f"Unexpected response format: {response}")
    except Exception as e:
        print(f"Error retrieving freq: {e}")
        return None

def windup_freq(instrument, start_voltage, step_size, delay):
    present_voltage_val = present_freq(instrument)
    step_size = abs(step_size) if present_voltage_val < start_voltage else -abs(step_size)
    while abs(present_voltage_val - start_voltage) > abs(step_size) / 2:
        new_voltage = present_voltage_val + step_size
        new_voltage = start_voltage if (step_size > 0 and new_voltage > start_voltage) or (step_size < 0 and new_voltage < start_voltage) else new_voltage
        #instrument.write(f"S{new_voltage:.6f}E")
        instrument.write(f'FREQ {new_voltage}')
        print(f"Wind-up freq to: {new_voltage:.3f} Hz")
        #print(f"Power increased from {current_power:.3f} dBm to {new_power:.3f} dBm")
        time.sleep(delay)
        present_voltage_val = present_freq(instrument)
    instrument.write(f'FREQ{start_voltage}')
    print(f"Final freq set to: {start_voltage:.3f} Hz")
    
def present_Prf(instrument):
    try:
        response = instrument.query("POW?")  # Note the '?' to query the value
        #match = re.search(r'([+-]?\d+\.\d+)', response)
        match = re.search(r'([+-]?\d+\.\d+E[+-]\d+)', response)
        if match:
            return float(match.group(1))
        else:
            raise ValueError(f"Unexpected response format: {response}")
    except Exception as e:
        print(f"Error retrieving power: {e}")
        return None

def windup_Prf(instrument, start_voltage, step_size, delay):
    present_voltage_val = present_Prf(instrument)
    step_size = abs(step_size) if present_voltage_val < start_voltage else -abs(step_size)
    while abs(present_voltage_val - start_voltage) > abs(step_size) / 2:
        new_voltage = present_voltage_val + step_size
        new_voltage = start_voltage if (step_size > 0 and new_voltage > start_voltage) or (step_size < 0 and new_voltage < start_voltage) else new_voltage
        #instrument.write(f"S{new_voltage:.6f}E")
        instrument.write(f'POW {new_voltage}')
        print(f"Wind-up power to: {new_voltage:.3f} dBm")
        #print(f"Power increased from {current_power:.3f} dBm to {new_power:.3f} dBm")
        time.sleep(delay)
        present_voltage_val = present_Prf(instrument)
    instrument.write(f'POW{start_voltage}')
    print(f"Final voltage set to: {start_voltage:.3f} dBm")
    
# =============================================================================
# try:
#     windup_Prf(instrument, start_voltage, step_size, delay)
#     power = present_Prf(instrument)
#     if power is not None:
#         print(f"Current Power: {power} dBm")
# except Exception as e:
#     print(f"An error occurred: {e}")
# finally:
#     instrument.close()
#     rm.close()
# =============================================================================


# In[ ]:


def main():

    instrument = open_resource(E4432B_address) #rf source
    

    start_voltage5, step_size5, delay5 = 0.0, 0.1, 0.2  #Prf
    start_voltage6, step_size6, delay6 = 1e9, 1e4, 0.2  #freq


    windup_Prf(instrument, start_voltage5, step_size5, delay5) #Prf
    windup_freq(instrument, start_voltage6, step_size6, delay6)#freq

    voltage5 = present_Prf(instrument)
    voltage6 = present_freq(instrument)

    print(f"Starter voltage5: {voltage5:.6f} Hz")
    print(f"Starter voltage6: {voltage6:.3f} dBM")
    



if __name__ == "__main__":
    main()
