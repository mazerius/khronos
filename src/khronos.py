### Main script to start up Khronos.

from src.cps_communication.DataParser import *
from src.storage.InfluxDBWriter import *
from src.time_management.Scheduler import *
from src.application_management.Updater import *
from flask import Flask, request
from flask_restful import Resource, Api
import Pyro4
from src.cps_communication.NetworkMonitor import *
import datetime



app = Flask(__name__)
api = Api(app)


############# Initialization ###########
print(datetime.datetime.now(), "| [Main]: Khronos started...")
print(datetime.datetime.now(), "| [Main]: Loading configurations...")
with open(os.path.join(os.path.join(os.getcwd(), 'configuration'), 'general_config')) as json_data_file:
    data = json.load(json_data_file)
    address = data["khronos"]["flask_address"]
    port = data["khronos"]["port"]

with open(os.path.join(os.path.join(os.getcwd(), 'configuration'), 'gm_config')) as json_data_file:
    data = json.load(json_data_file)
    gateway_address = data["gateway_manager"]["address"]
    gateway_port = data["gateway_manager"]["port"]


print(datetime.datetime.now(), "| [Main]: Instantiating core dependencies...")
influxdb_client = InfluxDBWriter(os.path.join(os.getcwd(),'configuration'))
data_parser = DataParser(influxdb_client)
network_monitor = NetworkMonitor(gateway_address, gateway_port)
updater = Updater()
scheduler = Scheduler(updater, data_parser, network_monitor)
data_parser.setScheduler(scheduler)


############# Khronos API #############

# used by GatewayManager to register discovered CPS devices
class registerDeviceAPI(Resource):
    def put(self):
        device = request.get_json()
        if not device["type"] == "uManager":
            network_monitor.registerDevice(device)
        else:
            network_monitor.registerGateway(device)
        return device['mac'] + 'has been successfully registered.', 200


#### used by GatewayManager to publish sensor data for CPS devices linked to application constraints / static timeouts.
class publishSensorDataAPI(Resource):
    def put(self):
        data = request.get_json()
        data_parser.receiveData(data)

### used by external applications to obtain a list of discovered CPS devices
class availableDevicesAPI(Resource):
    def get(self):
        response = []
        for pub in network_monitor.getPublishers():
            response.append(pub.toJSON())
        return response

### used by external applications to obtain a device by ID.
class deviceByIdAPI(Resource):
    def get(self, device_id):
        for device in network_monitor.getDevices():
            if device["id"] == int(device_id):
                return device
        return "not found", 404, {'Access-Control-Allow-Origin': '*'}


### used by external applications to register a completeness constraint for a CPS device data stream.
### currently, the device is identified by four parameters: pid1, pid2, mac address and measurement.
class registerCompletenessAPI(Resource):
    def put(self, pid1, pid2, mac, measurement, constraint, threshold, remote_object_uri):
        proxy = Pyro4.Proxy(remote_object_uri)
        scheduler.registerCompleteness(mac, pid1, pid2, measurement, proxy, constraint, threshold)


### used by external applications to register a static timeout for a CPS device data stream.
class registerTimeOutAPI(Resource):
    def put(self, pid1, pid2, mac, measurement, timeout, remote_object_uri):
        proxy = Pyro4.Proxy(remote_object_uri)
        scheduler.registerTimeOut(mac, pid1, pid2, measurement, proxy, timeout)



print(datetime.datetime.now(), "| [Main]: Adding API resources...")
api.add_resource(registerDeviceAPI, '/register_device')
api.add_resource(availableDevicesAPI, '/devices')
api.add_resource(deviceByIdAPI, '/device/<string:device_id>')
api.add_resource(publishSensorDataAPI, '/publish')
api.add_resource(registerCompletenessAPI, '/registerCompletenessConstraint/<string:pid1>/<string:pid2>/<string:mac>/<string:measurement>/<string:constraint>/<string:threshold>/<string:remote_object_uri>')
api.add_resource(registerTimeOutAPI, '/registerTimeout/<string:pid1>/<string:pid2>/<string:mac>/<string:measurement>/<string:timeout>/<string:remote_object_uri>')
app.run(host=address, port=port)

