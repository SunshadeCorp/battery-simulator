#!/usr/bin/env python3
import threading
import time
from pathlib import Path
from threading import Lock
from time import sleep
from tokenize import Double
from typing import Dict, Any, List

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
    def __init__(self, cell_number: int) -> None:
        self.cell_number = cell_number
        self.chip_temp = 24.0
        self.module_temp_1 = 24.0
        self.module_temp_2 = 24.0
        self.cell_voltages: List[float] = []
        self.cell_balancing: List[bool] = []

        for i in range(0, self.cell_number):
            self.cell_voltages.append(3.3)
            self.cell_balancing.append(False)

    def advance(self):
        pass

    def module_voltage(self) -> float:
        sum: float = 0.0
        for i in range(0, self.number_of_serial_cells):
            sum += self.cell_voltages[i]
        return sum

class BatterySimulator:
    def __init__(self, cell_number, module_number):
        self.start_time = time.time()
        self.cell_number : int = cell_number
        self.module_number : int = module_number
        self.modules: List[Battery] = []

        for i in range(0, self.cell_number):
            self.cell_voltages.append(3.3)
            self.cell_balancing.append(False)

    def uptime(self) -> int:
        return time.time() - self.start_time

    def loop(self):
        for bat_id in range(0, self.module_number):
            self.mqtt_client.publish(f'esp-module/{bat_id}/uptime', self.uptime(), retain=True)
            self.mqtt_client.publish(f'esp-module/{bat_id}/module_voltage', self.modules[bat_id].module_voltage(), retain=True)
            self.mqtt_client.publish(f'esp-module/{bat_id}/module_temps', self.modules[bat_id].module_temps(), retain=True)
            self.mqtt_client.publish(f'esp-module/{bat_id}/chip_temp', self.modules[bat_id].chip_temp, retain=True)
            self.mqtt_client.publish(f'esp-module/{bat_id}/timediff', 'xyz', retain=True)

            for cell_id in range(0, self.cell_number):
                self.mqtt_client.publish(f'esp-module/{bat_id}/cell/{cell_id}/is_balancing', self.modules[bat_id].cell_balancing[cell_id], retain=True)
                self.mqtt_client.publish(f'esp-module/{bat_id}/cell/{cell_id}/voltage', self.modules[bat_id].cell_voltages[cell_id], retain=True)

if __name__ == '__main__':
    battery_simulator = BatterySimulator(12, 12)
    battery_simulator.loop()