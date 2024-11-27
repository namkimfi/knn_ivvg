#testAI/091924iv_liveplot
#I-V code by Claude
#working
import pyvisa
import numpy as np
import matplotlib.pyplot as plt
import time

# Initialize VISA resource manager
rm = pyvisa.ResourceManager()

# Connect to instruments
voltage_source = rm.open_resource("GPIB0::02::INSTR")  # Yokogawa 7651
current_meter = rm.open_resource("GPIB0::22::INSTR")  # Agilent 34410A

# Reset instruments
#voltage_source.write("*RST")
#current_meter.write("*RST")
current_meter.write('*CLS')
current_meter.write('*RST')
current_meter.write('SENSe:RESistance:RANGe:AUTO ON')
current_meter.write('SENSe:VOLTage:DC:IMPedance:AUTO ON')

# Configure voltage source
#voltage_source.write("SOUR:FUNC VOLT")
#voltage_source.write("SOUR:VOLT:RANG 10")  # Set voltage range to 10V

# Configure current meter
#current_meter.write("CONF:CURR:DC")
#current_meter.write("CURR:RANG 1")  # Set current range to 1A

# Set up measurement parameters
start_voltage = 0
end_voltage = 0.5
step_voltage = 0.1
delay = 0.1  # Delay between measurements in seconds

voltages = np.arange(start_voltage, end_voltage + step_voltage, step_voltage)
currents = []
yokovoltages=[]



# Perform measurements
for voltage in voltages:
    # Set voltage
    voltage_source.write(f'S{voltage:0.5f}E')
    #voltage_source.write("OUTP ON")
    
    # Wait for settling
    time.sleep(delay)
    
    # Measure current
    current = float(current_meter.query("READ?"))
    currents.append(current)
    yokovoltages.append(voltage)
    
    print(f"Voltage: {voltage:.3f} V, Current: {current:.6f} A")
    
    # Plot the data
    plt.figure(figsize=(10, 6))
    plt.plot(yokovoltages, currents, 'b-o')
    plt.title("I-V Characteristic Curve")
    plt.xlabel("Voltage (V)")
    plt.ylabel("Current (A)")
    plt.grid(True)
    #plt.savefig("")
    plt.show()

# Turn off output
#voltage_source.write("OUTP OFF")

# Close connections
#voltage_source.close()
#current_meter.close()

# Plot the data
#plt.figure(figsize=(10, 6))
#plt.plot(voltages, currents, 'b-o')
#plt.title("I-V Characteristic Curve")
#plt.xlabel("Voltage (V)")
#plt.ylabel("Current (A)")
#plt.grid(True)
#plt.show()

# Save data to file
np.savetxt("iv_data.csv", np.column_stack((voltages, currents)), delimiter=",", header="Voltage (V),Current (A)", comments="")
print("Data saved to 'iv_data.csv'")