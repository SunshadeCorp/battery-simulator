#!/usr/bin/env python3
from cmath import pi
import threading
import time
import sched
from pathlib import Path
from threading import Lock
from time import sleep
from tokenize import Double
from typing import Dict, Any, List
from datetime import datetime

import paho.mqtt.client as mqtt
import yaml

'''
Routes to publish:
uptime
module_voltage
module_temps
chip_temp
timediff
cell/{id}/is_balancing
cell/{id}/voltage

Routes to subscribe:
measure_total_voltage
measure_total_current
set_config
balancing request
'''

class Battery:
    def __init__(self, num_cells: int) -> None:
        self.num_cells = num_cells
        self.chip_temp = 24.0
        self.module_temp_1 = 24.0
        self.module_temp_2 = 24.0
        #self.cell_voltages: List[float] = []
        self.cell_balancing: List[bool] = []

        for i in range(0, self.num_cells):
            #self.cell_voltages.append(3.3)
            self.cell_balancing.append(False)

    def module_voltage(self) -> float:
        sum: float = 0.0
        for i in range(0, self.num_cells):
            sum += self.cell_voltages[i]
        return sum

    def cell_voltage(self, cell_id) -> float:
        now = datetime.now()
        seconds_since_midnight = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
        percent_day = seconds_since_midnight / (24*60*60.0)
        voltage_half_full = 3.678
        voltage_range = 0.5
        cycle_offset = pi # maximum discharge at midnight, start charging at 6 am
        return (voltage_half_full - voltage_range / 2.0) + sin(percent_day*2*pi + cycle_offset)*voltage_range


class BatterySimulator:
    def __init__(self, num_cells, num_modules):
        self.start_time = time.time()
        self.num_cells : int = num_cells
        self.num_modules : int = num_modules
        self.modules: List[Battery] = []

        for i in range(0, num_modules):
            self.modules.append(Battery(num_cells))

    def uptime(self) -> int:
        return time.time() - self.start_time

    def mqtt_publish(self):
        print("ijoo")
        for bat_id in range(0, self.num_modules):
            self.mqtt_client.publish(f'esp-module/{bat_id}/uptime', self.uptime(), retain=True)
            self.mqtt_client.publish(f'esp-module/{bat_id}/module_voltage', self.modules[bat_id].module_voltage(), retain=True)
            self.mqtt_client.publish(f'esp-module/{bat_id}/module_temps', self.modules[bat_id].module_temps(), retain=True)
            self.mqtt_client.publish(f'esp-module/{bat_id}/chip_temp', self.modules[bat_id].chip_temp, retain=True)
            self.mqtt_client.publish(f'esp-module/{bat_id}/timediff', 'xyz', retain=True)

            for cell_id in range(0, self.num_cells):
                self.mqtt_client.publish(f'esp-module/{bat_id}/cell/{cell_id}/is_balancing', self.modules[bat_id].cell_balancing[cell_id], retain=True)
                self.mqtt_client.publish(f'esp-module/{bat_id}/cell/{cell_id}/voltage', self.modules[bat_id].cell_voltage(cell_id), retain=True)

def mqtt_job(sc):
    battery_simulator.mqtt_publish()
    scheduler.enter(3, 1, mqtt_job, (sc,))

battery_simulator = BatterySimulator(12, 12)
scheduler = sched.scheduler = sched.scheduler(time.time, time.sleep)

if __name__ == '__main__':
    scheduler.enter(3, 1, mqtt_job, (scheduler,))
    scheduler.run()