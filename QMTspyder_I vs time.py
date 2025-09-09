#graceful kill with live plotting (IHLee)
import pyvisa
import time
import numpy as np
import matplotlib.pyplot as plt
from contextlib import contextmanager
import signal
import threading
from IPython.display import clear_output

# ... [Previous class definitions for GracefulKiller, InstrumentManager, and CurrentMeter remain the same]

class GracefulKiller:
    def __init__(self):
        self.kill_now = False
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args):
        print("\nReceived stop signal. Starting graceful shutdown...")
        self.kill_now = True

class VoltageController:
    def __init__(self, instrument, name):
        self.instrument = instrument
        self.name = name
        self.current_voltage = 0

    def step_voltage(self, target_voltage, step_size=0.01, delay=0.1):
        print(f"Stepping {self.name} voltage from {self.current_voltage:.3f}V to {target_voltage:.3f}V")
        num_steps = max(int(abs(target_voltage - self.current_voltage) / step_size), 1)
        voltages = np.linspace(self.current_voltage, target_voltage, num_steps)
        
        for voltage in voltages:
            try:
                self.instrument.write(f'S{voltage:.5f}E')
                self.current_voltage = voltage
                print(f"{self.name} voltage set to {voltage:.5f}V")
                time.sleep(delay)
            except Exception as e:
                print(f"Error setting voltage for {self.name}: {e}")
                return False
        return True

    def return_to_zero(self):
        return self.step_voltage(0, step_size=0.05, delay=0.1)

# class CurrentMeter:
    # def __init__(self, instrument):
    #     self.instrument = instrument
    #     self.configure()

    # def configure(self):
    #     commands = [
    #         '*CLS',
    #         '*RST',
    #         'SENSe:RESistance:RANGe:AUTO ON',
    #         'SENSe:VOLTage:DC:IMPedance:AUTO ON'
    #     ]
    #     for cmd in commands:
    #         self.instrument.write(cmd)

    # def measure(self):
    #     return float(self.instrument.query("Read?"))
    #     #current = float(dmm.query("fetch?"))
    #     #return float(self.instrument.query("fetch?"))



class CurrentMeter:
    def __init__(self, instrument):
        self.instrument = instrument
        self.configure()

    def configure(self):
        """
        Resets the multimeter, configures it for a DC current measurement,
        and then tells it to start measuring continuously.
        """
        commands = [
            '*CLS',                             # Clear Status register
            '*RST',                             # Reset the instrument to defaults
            'SENSe:FUNCtion "CURR"',            # Set the measurement function to Current
            'SENSe:CURRent:RANGe:AUTO ON',      # Enable auto-ranging for the best precision
            'TRIGger:SOURce IMMediate',         # Set the trigger to happen instantly
            'INITiate:CONTinuous ON'            # **Key command: Start continuous measurements**
        ]
        for cmd in commands:
            self.instrument.write(cmd)
        
        # Give the instrument a moment to process the setup and start measuring
        time.sleep(1)

    def measure(self):
        """
        Fetches the latest completed measurement from the instrument's memory.
        This is much faster than initiating a new measurement each time.
        """
        return float(self.instrument.query("FETCh?"))

class DataCollector:
    def __init__(self):
        self.currents = []
        self.timestamps = []
        self.start_time = None

    def start(self):
        self.start_time = time.time()

    def add_measurement(self, current):
        if self.start_time is None:
            raise RuntimeError("DataCollector not started")
        
        self.timestamps.append(time.time() - self.start_time)
        self.currents.append(current)

 
        
       
#Inho Lee    
    def plot(self, show=True, save_path=None):
        if len(self.timestamps) > 1 and len(self.currents) > 1:
            cmin = min(self.currents)
            cmin = cmin-np.abs(cmin)*0.1
            cmax = max(self.currents)
            cmax = cmax + np.abs(cmax)*0.1
            plt.figure(figsize=(10, 6))
            plt.plot(self.timestamps, self.currents, 'b-o')
            plt.title("Current vs Time Measurement")
            plt.xlabel("Time (s)")
            plt.ylabel("Current (A)")
            plt.ylim((cmin, cmax))
            plt.grid(True)
            if save_path:
                plt.savefig(save_path)
            if show:
                plt.show()
            plt.close()



    def save_data(self, filename="current_time_data.csv"):
        if not self.timestamps or not self.currents:
            print("No data to save.")
            return
        
        try:
            np.savetxt(
                filename,
                np.column_stack((self.timestamps, self.currents)),
                delimiter=",",
                header="Time (s),Current (A)",
                comments=""
            )
            print(f"Data saved to '{filename}'")
        except Exception as e:
            print(f"Error saving data: {e}")

def measurement_thread(killer, collector, interval, current_meter):
    while not killer.kill_now:
        current = current_meter.measure()
        if current is not None:
            collector.add_measurement(current)
            print(f"Time: {collector.timestamps[-1]:.2f} s, Current: {current:.6f} A")
        time.sleep(interval)

class InstrumentManager:
    def __init__(self):
        self.rm = pyvisa.ResourceManager()
        self.instruments = {}
        self.killer = GracefulKiller()

    def open_instrument(self, gpib_address, name):
        try:
            instrument = self.rm.open_resource(f'GPIB43::{gpib_address}::INSTR')
            self.instruments[name] = instrument
            return instrument
        except pyvisa.Error as e:
            raise ConnectionError(f"Failed to connect to {name} at GPIB43 {gpib_address}: {str(e)}")

    def close_all(self):
        for instrument in self.instruments.values():
            try:
                instrument.close()
            except:
                pass
        self.instruments.clear()


@contextmanager
def measurement_session():
    manager = InstrumentManager()
    try:
        yield manager
    finally:
        manager.close_all()

def run_measurement(duration=100000, interval=1):
    with measurement_session() as manager:
        yoko1 = VoltageController(manager.open_instrument(4, "YOKOgate1"), "YOKOgate1")
        yoko2 = VoltageController(manager.open_instrument(5, "YOKOgate2"), "YOKOgate2")
        current_meter = CurrentMeter(manager.open_instrument(19, "Current Meter"))
        collector = DataCollector()

        try:
            target_voltage1 = 0.4
            target_voltage2 = 0.5
            if not (yoko1.step_voltage(target_voltage1) and yoko2.step_voltage(target_voltage2)):
                return
            collector.start()
            thread = threading.Thread(target=measurement_thread, args=(manager.killer, collector, interval, current_meter))
            thread.start()
            timeout = time.time() + duration
            while time.time() < timeout and not manager.killer.kill_now:
                time.sleep(0.1)
                num_points = int(duration / interval)
                for i in range(num_points):
                    if manager.killer.kill_now:
                        break
                    current = current_meter.measure()
                    collector.add_measurement(current)
                    collector.plot()
                    print(f"Time: {collector.timestamps[-1]:.2f} s, Current: {current:.6f} A")
                    clear_output(wait=True)
                    remaining_interval = interval - (time.time() - collector.start_time - collector.timestamps[-1])
                    if remaining_interval > 0:
                        time.sleep(remaining_interval)
            
        except Exception as e:
            print(f"An error occurred: {str(e)}")
        finally:
            manager.killer.kill_now = True
            thread.join(timeout=5)
            
            print("Returning voltages to zero...")
            yoko1.return_to_zero()
            yoko2.return_to_zero()
            
            if collector.timestamps:
                collector.save_data()
                collector.plot()
            else:
                print("No data collected.")
            
            print("Measurement completed or interrupted. Shutting down.")
            collector.save_data()
            collector.plot()
if __name__ == "__main__":
    run_measurement()