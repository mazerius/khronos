### Main script to start up Khronos.

import Pyro4
from src.application_management.Updater import *
from src.cps_communication.DataParser import *
from src.cps_communication.NetworkMonitor import *
from src.time_management.Scheduler import *
from src.storage.InfluxDBWriter import *
from flask import Flask, request, jsonify
from flask_sockets import Sockets
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

app = Flask(__name__)
sockets = Sockets(app)



############# Initialization ###########
print(datetime.datetime.now(), "| [Main]: Khronos started...")
print(datetime.datetime.now(), "| [Main]: Loading configurations...")
with open(os.path.join(os.path.join(os.getcwd(), 'configuration'), 'general_config')) as json_data_file:
    data = json.load(json_data_file)
    flask_address = data["khronos"]["flask_address"]
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
publisher = Publisher()
scheduler = Scheduler(updater, publisher, data_parser, network_monitor)
data_parser.setScheduler(scheduler)


############# Khronos API #############

# used by GatewayManager to register discovered CPS devices
@app.route('/register_device',  methods=['PUT'])
def registerDevice():
    device = request.get_json()
    if not device["type"] == "uManager":
        network_monitor.registerDevice(device)
    else:
        network_monitor.registerGateway(device)
    return device['mac'] + 'has been successfully registered.', 200

### used by external applications to obtain a list of discovered CPS devices
@app.route('/devices', methods=['GET'])
def getDevices():
    response = []
    for pub in network_monitor.getDataSources():
        response.append(pub.toJSON())
    return response

### used by external applications to obtain a device by ID.
@app.route('/device/<string:device_id>', methods=['GET'])
def getDeviceByID(device_id):
    for device in network_monitor.getDevices():
        if device["id"] == int(device_id):
            return device
    return "not found", 404, {'Access-Control-Allow-Origin': '*'}

#### used by GatewayManager to publish sensor data for CPS devices linked to application constraints / static timeouts.
@app.route('/publish', methods=['PUT'])
def publishData():
    data = request.get_json()
    print('publish data:', data)
    data_parser.receiveData(data)
    return 'ok'

### used by external applications to register a completeness constraint for a CPS device data stream using RMI.
### currently, the device is identified by four parameters: pid1, pid2, mac address and measurement.
@app.route('/registerCompletenessConstraintRMI/<pid1>/<pid2>/<mac>/<measurement>/<constraint>/<threshold>/<remote_object_uri>', methods=['PUT'])
def registerCompletenessConstraintRMI(pid1,pid2,mac,measurement,constraint,threshold,remote_object_uri):
    proxy = Pyro4.Proxy(remote_object_uri)
    id = scheduler.registerCompleteness(mac, pid1, pid2, measurement, constraint, threshold, proxy)
    return id


### used by external applications to register a completeness constraint for a CPS device data stream.
### currently, the device is identified by four parameters: pid1, pid2, mac address and measurement.
@app.route('/registerCompletenessConstraint/<string:pid1>/<string:pid2>/<string:mac>/<string:measurement>/<string:constraint>/<string:threshold>',  methods=['PUT'])
def registerCompletenessConstraint(pid1,pid2,mac, measurement,constraint,threshold):
    print('registerCompletenessConstraint',pid1,pid2)
    id = scheduler.registerCompleteness(mac, pid1, pid2, measurement, constraint, threshold)
    print('id', id)
    return jsonify(id)

 ### used by external applications to register a static timeout for a CPS device data stream using RMI.
@app.route('/registerTimeoutRMI/<string:pid1>/<string:pid2>/<string:mac>/<string:measurement>/<string:timeout>/<string:remote_object_uri>',methods=['PUT'])
def registerTimeoutRMI(pid1, pid2, mac, measurement, timeout, remote_object_uri):
    proxy = Pyro4.Proxy(remote_object_uri)
    id = scheduler.registerTimeOut(mac, pid1, pid2, measurement, timeout, proxy)
    return id

### used by external applications to register a static timeout for a CPS device data stream.
@app.route('/registerTimeout/<string:pid1>/<string:pid2>/<string:mac>/<string:measurement>/<string:timeout>', methods=['PUT'])
def registerTimeout(pid1,pid2,mac,measurement,timeout):
    id = scheduler.registerTimeOut(mac, pid1, pid2, measurement, timeout)
    return jsonify(id)


@sockets.route('/khronos')
def acceptConnection(ws):
    publisher.addWebSocket(ws)
    while not ws.closed:
        message = ws.receive()
        print('publishing')
        ws.send(message)

print(datetime.datetime.now(), "| [Main]: Adding API resources...")
print(datetime.datetime.now(), "| [Main]: Running on...", flask_address, ":", port)
server = pywsgi.WSGIServer((flask_address, port), app, handler_class=WebSocketHandler)
server.serve_forever()

