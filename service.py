#!/usr/bin/env python3
from cmath import pi
import math
from pickletools import uint1
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
TODO:

- React to balancing request
- Simulate cell drift
'''


class Battery:
    def __init__(self, num_cells: int) -> None:
        self.num_cells = num_cells
        self.chip_temp = 24.0
        self.module_temp_1 = 24.0
        self.module_temp_2 = 24.0
        #self.cell_voltages: List[float] = []
        self.cell_balancing: List[int] = []
        self.measure_system_voltage = False
        self.measure_system_current = False
        self.module_name = None

        for i in range(0, self.num_cells):
            #self.cell_voltages.append(3.3)
            self.cell_balancing.append(0)

    def module_voltage(self) -> float:
        sum: float = 0.0
        for cell_id in range(0, self.num_cells):
            sum += self.cell_voltage(cell_id)
        return sum

    def module_temps(self) -> float:
        return "24,24"

    def cell_voltage(self, cell_id) -> float:
        now = datetime.now()
        seconds_since_midnight = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
        percent_day = seconds_since_midnight / (24*60*60.0)
        voltage_half_full = 3.678
        voltage_range = 0.5
        cycle_offset = pi # maximum discharge at midnight, start charging at 6 am
        return (voltage_half_full - voltage_range / 2.0) + math.sin(percent_day*2*pi + cycle_offset)*voltage_range


class BatterySimulator:
    def __init__(self, num_cells, num_modules):
        config = self.get_config('config.yaml')
        credentials = self.get_config('credentials.yaml')
        self.start_time = time.time()
        self.num_cells : int = num_cells
        self.num_modules : int = num_modules
        self.modules: List[Battery] = []
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.mqtt_on_connect
        self.mqtt_client.on_message = self.mqtt_on_message
        self.mqtt_client.username_pw_set(credentials['username'], credentials['password'])
        self.mqtt_client.connect(host=config['mqtt_server'], port=config['mqtt_port'], keepalive=60)
        self.mqtt_client.loop_start()

        for i in range(0, num_modules):
            self.modules.append(Battery(num_cells))

    @staticmethod
    def get_config(filename: str) -> Dict:
        with open(Path(__file__).parent / filename, 'r') as file:
            try:
                config = yaml.safe_load(file)
                print(config)
                return config
            except yaml.YAMLError as e:
                print(e)

    def mqtt_on_connect(self, client: mqtt.Client, userdata: Any, flags: Dict, rc: int):
        print("Sucessfully connected to MQTT")
        for bat_id in range(0, self.num_modules):
            for cell_id in range(0, self.num_cells):
                self.mqtt_client.subscribe(f'esp-module/bat-sim-{bat_id+1}/cell/{cell_id+1}/balance_request')
                self.mqtt_client.subscribe(f'esp-module/bat-sim-{bat_id+1}/set_config')
                self.mqtt_client.subscribe(f'esp-module/bat-sim-{bat_id+1}/blink')
                self.mqtt_client.subscribe(f'esp-module/bat-sim-{bat_id+1}/restart')
                

    def mqtt_on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage):
        print("Got MQTT message")
        for module_id in range(0, self.num_modules):
            if msg.topic == f'esp-module/bat-sim-{module_id+1}/set_config':
                payload = msg.topic.split(',')
                if payload.count == 3:
                    self.modules[module_id].module_name = payload[0]
                    self.modules[module_id].measure_system_voltage = (payload[1] == "1")
                    self.modules[module_id].measure_system_current = (payload[2] == "1")
                else:
                    print("set_config: invalid argument count")
            elif msg.topic == f'esp-module/bat-sim-{module_id+1}/blink':
                print(f'Module {module_id+1}: Blink Blink!')
            elif msg.topic == f'esp-module/bat-sim-{module_id+1}/restart':
                print(f'Module {module_id+1}: Restart')
            for cell_id in range(0, self.num_cells):
                if msg.topic == f'esp-module/{module_id+1}/cell/{cell_id+1}/balance_request':
                    self.modules[module_id].cell_balancing[cell_id] = 1

    def uptime(self) -> int:
        return time.time() - self.start_time

    def mqtt_publish(self):
        print("Publishing some values")
        for bat_id in range(0, self.num_modules):
            self.mqtt_client.publish(f'esp-module/bat-sim-{bat_id}/uptime', self.uptime(), retain=True)
            self.mqtt_client.publish(f'esp-module/bat-sim-{bat_id}/module_voltage', self.modules[bat_id].module_voltage(), retain=True)
            self.mqtt_client.publish(f'esp-module/bat-sim-{bat_id}/module_temps', self.modules[bat_id].module_temps(), retain=True)
            self.mqtt_client.publish(f'esp-module/bat-sim-{bat_id}/chip_temp', self.modules[bat_id].chip_temp, retain=True)

            for cell_id in range(0, self.num_cells):
                self.mqtt_client.publish(f'esp-module/bat-sim-{bat_id}/cell/{cell_id}/is_balancing', self.modules[bat_id].cell_balancing[cell_id], retain=True)
                self.mqtt_client.publish(f'esp-module/bat-sim-{bat_id}/cell/{cell_id}/voltage', self.modules[bat_id].cell_voltage(cell_id), retain=True)

def mqtt_job(sc):
    battery_simulator.mqtt_publish()
    scheduler.enter(3, 1, mqtt_job, (sc,))

battery_simulator = BatterySimulator(12, 12)
scheduler = sched.scheduler = sched.scheduler(time.time, time.sleep)

if __name__ == '__main__':
    scheduler.enter(3, 1, mqtt_job, (scheduler,))
    scheduler.run()