
import re
import ssl
import sys
import threading
import time
from json import dumps

import requests
import websocket
from flask import Flask, request
from flask_restful import Resource, Api
from requests.exceptions import ConnectionError
from src.time_management.StreamManager import *

from src.storage.InfluxDBWriter import *

############# Load configs ###############

os.chdir("..") #Go up one directory from working directory
config_path = os.path.join(os.getcwd(), 'configuration')
config_file = os.path.join(config_path, 'gm_config')
with open(config_file) as json_data_file:
    data = json.load(json_data_file)

gateway_address = data['gateway']['address']
gateway_port = data['gateway']['port']
gateway_manager_address = data['gateway_manager']['address']
gateway_manager_port = data['gateway_manager']['port']
refresh_period = data['gateway_manager']['discovery_refresh_period']


with open(os.path.join(os.path.join(os.getcwd(), 'configuration'), 'general_config')) as json_data_file:
    data = json.load(json_data_file)
    khronos_address = data["khronos"]["address"]
    khronos_port = data["khronos"]["port"]

khronos_url = 'http://' + khronos_address + ':' + str(khronos_port)



############## Helper functions ################

# Checks if given string satisfies format of a MAC address.
def checkMAC(x):
    if re.match("[0-9a-f]{2}([-:])[0-9a-f]{2}(\\1[0-9a-f]{2}){6}$", x.lower()):
        return True

    else:
        return False

# Used to encode set() into JSON.
class SetEncoder(json.JSONEncoder):
   def default(self, obj):
     if isinstance(obj, set):
        return list(obj)
     return json.JSONEncoder.default(self, obj)


### maintains CPS devices whose data should be forwarded to Khronos
data_sources = set()
data_sources_lock = threading.Lock()


# Initializing time managemente dependencies.
influxdb_client = InfluxDBWriter(os.path.join(os.getcwd(), 'configuration'))
stream_manager = StreamManager(influxdb_client)


############## Websocket Thread ################

class webSocketThread (threading.Thread):
   def __init__(self):
      threading.Thread.__init__(self)


   def run(self):
      print (datetime.datetime.now(),"| Starting " + self.name)
      connectToWebSocket()
      print (datetime.datetime.now(),"| Exiting " + self.name)


# checks if given peripheral is a data source
def checkPeripheralInDataSources(peripheral, mac):
    for publisher in data_sources:
        if ((peripheral + ':' + mac) in publisher):
            return True
    return False


# connects to the gateway websocket and listens for incoming raw sensor data.
def connectToWebSocket():
    print(datetime.datetime.now(), "| [GatewayManager]: Connecting to websocket...")
    websocket.enableTrace(True)
    while True:
        print(datetime.datetime.now(), "| [GatewayManager]: Attempting to create connection to websocket...")
        try:
            ws = websocket.create_connection("wss://" + gateway_address + ":" + str(gateway_port) + "/", sslopt={"cert_reqs": ssl.CERT_NONE})
            print(datetime.datetime.now(), "| [GatewayManager]: Successfully connected to websocket.")
            while True:
               result = ws.recv()
               headers = {'Content-Type': 'application/json'}
               result_json = json.loads(result)  # decode received message to JSON
               # check for sensor data from peripheral
               if (result_json['type'] == 'sensor-data'):
                   mac = result_json['contents']['mac']
                   peripheral_id = result_json['contents']['identifier']
                   # if peripheral has already been discovered
                   if not stream_manager.getStreamByID(peripheral_id, mac) == None:
                       thisStream = stream_manager.getStreamByID(peripheral_id, mac)
                       timestamp = result_json['contents']['timestamp']
                       time_to_write = datetime.datetime.utcfromtimestamp(1558356626234250/1000000.).strftime('%Y-%m-%dT%H:%M:%S.%f')
                       # update timeliness / completeness stats
                       ready_to_be_published = thisStream.increment(timestamp, time_to_write)
                       if (ready_to_be_published):
                        # construct payload to send to Khronos
                        result_json['next-timeout'] = thisStream.getNextTimeoutsForConstraints()
                        result_json['achieved-completeness-constraints'] = thisStream.getAchievedCompletenessForConstraints()
                        result_json['above-constraint'] = thisStream.getAboveConstraintForConstraints()
                        result_json['achieved-completeness-timeouts'] = thisStream.getAchievedCompletenessForStaticTimeouts()
                        # synchronized access to shared resource
                        with data_sources_lock:
                          # if the peripheral is in publishers, received data should be forwarded to Khronos
                          if checkPeripheralInDataSources(result_json['contents']['identifier'], result_json['contents']['mac']):
                               print(datetime.datetime.now(), "| [GatewayManager]: Forwarding received sensor data", result_json, "to Khronos.")
                               requests.put(khronos_url + '/publish', data=json.dumps(result_json), headers = headers)
                   else:
                       print(datetime.datetime.now(), "| [GatewayManager]: peripheral:" + peripheral_id + " for device mac:" + mac + "does not exist.")
        except ConnectionError as e:
            print(e)
            print(datetime.datetime.now(), "| [GatewayManager]: ConnectionError occured. Attempting to reconnect...")


############## deviceDiscovery Thread ################

# Periodically scans the CPS network for discovered devices and registers them to Khronos.
# Creates a Stream object per discovered device_mac / peripheral_id pair.
class deviceDiscoveryThread(threading.Thread):

    # converts string keys to float
    # e.g. converts "0.6":2.8 to 0.6:2.8.
    def cleanifyDictionary(self, dictionary):
        result = dict()
        for key in dictionary.keys():
            result[float(key)] = dictionary[key]
        return result



    # delay specifies the refresh period
    def __init__(self, delay):
        threading.Thread.__init__(self)
        self.delay = delay
        self.devices = set()
        with open(os.path.join(os.path.join(os.getcwd(), 'configuration'), 'general_config')) as json_data_file:
            data = json.load(json_data_file)
            self.alpha = data['prediction_technique']['alpha']
            self.beta = data['prediction_technique']['beta']
            self.constraints_to_K = self.cleanifyDictionary(data['prediction_technique']['K'])
            self.window_size = data['prediction_technique']['window_size']

    def run(self):
        print(datetime.datetime.now(), "| [GatewayManager]: Discovering Devices...")
        base_url = 'https://' + gateway_address + ':' + str(gateway_port) + '/api/v1/devices'
        while True:
            try:
                print(datetime.datetime.now(),'| [GatewayManager]: Trying requests.get(' + base_url + ')')
                response = requests.get(base_url, verify= False)
                result = response.json()
                print(datetime.datetime.now(),'| [GatewayManager]: Discovered', result)
                for device in result:
                    # if device is not previously discovered and active
                    if device['status'] != 'UNKNOWN' and device['status'] != "LOST" and device['mac'] not in self.devices:
                        print(datetime.datetime.now(),'| [GatewayManager]: adding newly discovered device', device['mac'])
                        self.devices.add(device['mac'])
                        for peripheral in device['peripherals']:
                            # if the peripheral does not exist
                            if not stream_manager.streamExists(peripheral['identifier'], device['mac']):
                                # used for prediction technique, same as RTO values in TCP
                                # if the device transmits periodically (has a sampling rate)
                                if 'sampling_rate' in peripheral:
                                    stream_manager.createStream(peripheral['identifier'], device['mac'], self.alpha, self.beta, influxdb_client, self.constraints_to_K, self.window_size)
                                    print(datetime.datetime.now(), '| [GatewayManager]: registered Stream ' + peripheral['identifier'] + ':' + device['mac'] + ' @ StreamManager')
                        headers = {'Content-Type' : 'application/json'}
                        requests.put(khronos_url + '/register_device', data=json.dumps(device), headers=headers)
                time.sleep(self.delay)
            except ConnectionError as e:
                print(e)
                print(datetime.datetime.now(), "| [Gateway Manager]: DeviceDiscoveryThread failed, retrying...")
        print(datetime.datetime.now(), '| [GatewayManager]:', "Exiting " + self.name)



############## RESTful API thread ################

# Responsible for providing the Khronos REST API to external applications.
class RESTfulAPIThread (threading.Thread):
   def __init__(self):
      threading.Thread.__init__(self)


   def run(self):
      print(datetime.datetime.now(), "| Starting RESTfulAPIThread...")
      runRESTfulAPI()
      print(datetime.datetime.now(), "| Exiting RESTfulAPIThread... ")

def runRESTfulAPI():

    app = Flask(__name__)
    api = Api(app)

    base_url = 'https://' + gateway_address + ':' + str(gateway_port) + '/api/v1/devices'
    network_url = 'https://' + gateway_address + ':' + str(gateway_port) + '/api/v1/network'


    ######## API to enable Khronos components to obtain information about the CPS network. ##########
    # These commands are implemented to work with a VersaSense gateway.
    # In case of a different network, consult the gateway's documentation.


    # requests an overview of the entire CPS cps_communication
    class NetworkAPI(Resource):
        def get(self):
            response = requests.get(network_url)
            result = response.json()
            return result

    # requests information for an individual device in the CPS network
    class NetworkDeviceAPI(Resource):
        def get(self,device_mac):
            response = requests.get(network_url)
            result = response.json()
            for device in result['devices']:
                if device_mac == device['mac']:
                    return device
            return device_mac + 'not found in network', 400

    # requests information for the underlying devices in the CPS network
    class DevicesAPI(Resource):
        def get(self):
            response = requests.get(base_url)
            result = response.json()
            return result

    # requests information for a specific device (VersaSense device) in the CPS network
    class DeviceByIdAPI(Resource):
        def get(self, device_mac):
            response = requests.get(base_url + '/' + device_mac)
            result = response.json()
            return result

        def put(self, device_mac):
            name_description_location = (request.form).to_dict(flat=True)
            response = requests.put(base_url + '/' + device_mac, name_description_location)
            return response.text


        def delete(self, device_mac):
            response = requests.delete(base_url + '/' + device_mac)
            return response.text

    # requests information for peripherals in the CPS network
    class PeripheralsAPI(Resource):
        def get(self, device_mac):
            response = requests.get(base_url + '/' + device_mac + '/peripherals')
            result = response.json()
            return result

    # requests information for a specific peripheral in the CPS network
    class PeripheralAPI(Resource):
        def get(self, device_mac, pid1, pid2):
            response = requests.get(base_url + '/' + device_mac + '/peripherals' + '/' + pid1 + '/' + pid2)
            return response.text


    class PeripheralRateAPI(Resource):

        # requests information about a peripheral's sampling rate.
        def get(self, device_mac, pid1, pid2):
            response = requests.get(base_url + '/' + device_mac + '/peripherals' + '/' + pid1 + '/' + pid2 + '/rate')
            result = response.text
            return result

        # sets the sampling rate of a specific peripheral.
        def put(self, device_mac, pid1, pid2):
            rate = (request.form).to_dict(flat=True)
            response = requests.put(base_url + '/' + device_mac + '/peripherals' + '/' + pid1 + '/' + pid2 + '/rate', rate)
            return response.text


    class PeripheralDataAPI(Resource):
        # requests a sample from a peripheral.
        def get(self, device_mac, pid1, pid2):
            response = requests.get(base_url + '/' + device_mac + '/peripherals' + '/' + pid1 + '/' + pid2 + '/sample')
            return response.text

        # sends an actuation command to a peripheral
        def put(self, device_mac, pid1, pid2):
            contents = request.form.to_dict(flat=True)
            response = requests.put(base_url + '/' + device_mac + '/peripherals' + '/' + pid1 + '/' + pid2 + '/actuate', contents)
            return response.text

    # returns the registered data sources
    class DataSourcesAPI(Resource):
        def get(self):
            with data_sources_lock:
                data = dumps(data_sources, cls=SetEncoder)
            return data, 200

    ## enables Khronos to activate data sources -> corresponding sensor_data will now be forwarded.
    class ActivateDataSourceAPI(Resource):
        def put(self, pid1, pid2, mac, measurement):
            device = pid1 + '/' + pid2 + ':' + mac + '|' + measurement
            if (not checkMAC(mac)):
                print(datetime.datetime.now(), '| [GatewayManager]:', mac, 'is not a valid MAC address.')
                return mac + 'is invalid MAC address.', 400
            else:
                with data_sources_lock:
                    if not device in data_sources:
                        print(datetime.datetime.now(), '| [GatewayManager]: activated', device, 'successfully.')
                        data_sources.add(device)
                        return device+ 'activated successfully.', 200
                    else:
                        print(datetime.datetime.now(), '| [GatewayManager]:', device, 'is already activated.')
                        return device + 'already activated', 200



    # keeps track of completeness statistics for registered static timeout
    class TrackStaticTimeoutAPI(Resource):
        def put(self, device_mac, pid1, pid2, timeout):
            peripheral_id = pid1 + '/' + pid2
            print(datetime.datetime.now(),'| [GatewayManager]: tracking static timeout for', peripheral_id + ':' + device_mac, 'with value:', timeout)
            stream_manager.trackStaticTimeout(peripheral_id, device_mac, timeout)

    # keeps track of timeliness / completeness statistics for registered completeness constraint
    class TrackCompletenessConstraintAPI(Resource):
        def put(self, device_mac, pid1, pid2, constraint):
            peripheral_id = pid1 + '/' + pid2
            print(datetime.datetime.now(),'| [GatewayManager]: tracking completeness constraint for', peripheral_id + ':' + device_mac, 'with value:', constraint)
            stream_manager.trackCompletenessConstraint(peripheral_id, device_mac, constraint)



    ############## Register #############

    # completeness / timeliness resources
    api.add_resource(TrackStaticTimeoutAPI, '/trackStaticTimeout/<string:device_mac>/<string:pid1>/<string:pid2>/<string:timeout>')
    api.add_resource(TrackCompletenessConstraintAPI, '/trackCompletenessConstraint/<string:device_mac>/<string:pid1>/<string:pid2>/<string:constraint>')
    api.add_resource(DataSourcesAPI, '/publishers')
    api.add_resource(ActivateDataSourceAPI, '/activate-publisher/<string:pid1>/<string:pid2>/<string:mac>/<string:measurement>')


    # CPS cps_communication / devices resources
    api.add_resource(DevicesAPI, '/devices')
    api.add_resource(NetworkAPI, '/network')
    api.add_resource(PeripheralsAPI, '/peripherals/<string:device_mac>')
    api.add_resource(PeripheralAPI, '/peripheral/<string:device_mac>/<string:pid1>/<string:pid2>')
    api.add_resource(PeripheralRateAPI, '/peripheral_rate/<string:device_mac>/<string:pid1>/<string:pid2>')
    api.add_resource(PeripheralDataAPI, '/peripheral_data/<string:device_mac>/<string:pid1>/<string:pid2>')
    api.add_resource(DeviceByIdAPI, '/device/<string:device_mac>')
    api.add_resource(NetworkDeviceAPI, '/network_parameters/<string:device_mac>')
    app.run(host=gateway_manager_address, port=gateway_manager_port)




if __name__ == '__main__':
    # refresh discovered devices every minute
    deviceDiscoveryThread = deviceDiscoveryThread(refresh_period)
    deviceDiscoveryThread.setDaemon(True)
    print(datetime.datetime.now(),'[GatewayManager]: starting DeviceDiscovery thread with a delay of', refresh_period, 'seconds.')
    deviceDiscoveryThread.start()
    websocketThread = webSocketThread()
    websocketThread.setDaemon(True)
    print(datetime.datetime.now(), '[GatewayManager]: starting WebSocket thread.')
    websocketThread.start()
    RESTfulAPIThread = RESTfulAPIThread()
    RESTfulAPIThread.setDaemon(True)
    print(datetime.datetime.now(), '[GatewayManager]: starting RESTfulAPI thread.')
    RESTfulAPIThread.start()
    while(True):
        inp = input(str(datetime.datetime.now()) + '[GatewayManager]: Type `exit` to quit ')
        if (inp == 'exit'):
            try:
                print(datetime.datetime.now(), "[GatewayManager]: Exiting...")
                sys.exit(0)
            except SystemExit:
                os._exit(0)
