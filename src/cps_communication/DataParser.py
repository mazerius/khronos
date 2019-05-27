## A class responsible for parsing incoming sensor data from the GatewayManager.

import datetime
import math
class DataParser:

    def __init__(self, influxDBWriter=None):
        self.scheduler = None
        self.influxDBWriter = influxDBWriter


    def setScheduler(self, scheduler):
        self.scheduler = scheduler

    # invoked by GatewayManager through Khronos API whenever sensor data is published
    def receiveData(self,data):
        arrival_time = datetime.datetime.now()
        for item in data['contents']['data']:
            print(datetime.datetime.now(), '| [DataParser]: received sensor data:', data, 'at', arrival_time)
            measurement = item['measurement']
            value = item['value']
            key = data['contents']['identifier'] + ':' + data['contents']['mac'] + "|" + measurement
            time_generated = math.ceil(item['timestamp'] / 10 ** 6)
            self.scheduler.receiveData(arrival_time, time_generated, key, value, data['next-timeout'], data['achieved-completeness-constraints'], data['below-constraint'], data['achieved-completeness-timeouts'])

