import requests

from src.cps_communication.DataSource import *


## Responsible for communication between the GatewayManager and internal components of Khronos.
class NetworkMonitor:


    def __init__(self, gateway_address, gateway_port):
        self.gateway_URL = 'http://' + gateway_address + ':' + str(gateway_port)
        # list of registered data sources in the CPS network
        self.data_sources = list()
        self.gateways = list()


    ## register peripherals as a data source
    def registerDevice(self, device):
        device['id'] = len(self.data_sources)
        for peripheral in device['peripherals']:
            for measurement in peripheral['measurements']:
                self.createDataSource(peripheral['identifier'], device['mac'], measurement)


    def createDataSource(self, peripheral_id, device_mac, measurement):
        id = peripheral_id + ":" + device_mac + "|" + measurement['name']
        datatype = measurement['datatype']
        if 'unit' in measurement :
            unit = measurement['unit']
        else:
            unit = None
        self.data_sources.append(DataSource(id, id, datatype, unit))

    # notifies GatewayManager to forward sensor data to Khronos from this data source
    def activateDataSource(self, publisher_name):
        pid1 = publisher_name.split('/')[0]
        pid2 = publisher_name.split('/')[1].split(':')[0]
        mac = publisher_name.split(':')[1].split('|')[0]
        measurement = publisher_name.split('|')[1]
        for publisher in self.getDataSources():
            if publisher.getName() == publisher_name:
                requests.put(self.gateway_URL + '/activate-publisher/' + pid1 + '/' + pid2 + '/' + mac + '/' + measurement)

    # returns the list of data sources
    def getDataSources(self):
        return self.data_sources

    # returns the list of registered gateways
    def getGateways(self):
        return self.gateways

    # registers a uManager gateway to the system.
    def registerGateway(self, gateway):
        self.gateways.append(gateway)

    # invoked when a static timeout is registered by an application
    def trackStaticTimeoutForStream(self, key, time_window):
        time_window = str(time_window)
        key = key.split(':')
        pid1 = key[0].split('/')[0]
        pid2 = key[0].split('/')[1]
        device_mac = key[1].split('|')[0]
        requests.put(self.gateway_URL + '/trackStaticTimeout' + '/' + device_mac + '/' + pid1 + '/' + pid2 + '/' + time_window)

    # invoked when a completeness constraint is registered by an application
    def trackCompletenessConstraintForStream(self, key, constraint):
        constraint = str(constraint)
        key = key.split(':')
        pid1 = key[0].split('/')[0]
        pid2 = key[0].split('/')[1]
        device_mac = key[1].split('|')[0]
        requests.put(self.gateway_URL + '/trackCompletenessConstraint' + '/' + device_mac + '/' + pid1 + '/' + pid2 + '/' + constraint)


    def notifyTimeoutForConstraint(self, key, constraint):
        constraint = str(constraint)
        key = key.split(':')
        pid1 = key[0].split('/')[0]
        pid2 = key[0].split('/')[1]
        device_mac = key[1].split('|')[0]
        return requests.get(self.gateway_URL + '/notify-timeout-constraint' + '/' + device_mac + '/' + pid1 + '/' + pid2 + '/' + constraint)

    def notifyTimeoutForStaticTimeout(self, key, timeout):
        timeout = str(timeout)
        key = key.split(':')
        pid1 = key[0].split('/')[0]
        pid2 = key[0].split('/')[1]
        device_mac = key[1].split('|')[0]
        return requests.get(self.gateway_URL + '/notify-timeout-static' + '/' + device_mac + '/' + pid1 + '/' + pid2 + '/' + timeout)
