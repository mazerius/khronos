# responsible for publishing events on websockets, when instructed by the Scheduler.

from src.application_management.WebSocketThread import WebSocketThread
import json
import os
from src.application_management.WebSocketThread import WebSocketServerThread



class Publisher:

    def __init__(self):

        ############# Load configs ###############
        config_path = os.path.join(os.getcwd(), 'configuration')
        config_file = os.path.join(config_path, 'general_config')
        with open(config_file) as json_data_file:
            data = json.load(json_data_file)

        ws_on_next_address = data['application_management']['websocket_on_next_address']
        ws_on_next_port = data['application_management']['websocket_on_next_port']
        ws_on_timeout_address = data['application_management']['websocket_on_timeout_address']
        ws_on_timeout_port = data['application_management']['websocket_on_timeout_port']
        ws_on_violation_address = data['application_management']['websocket_on_violation_address']
        ws_on_violation_port = data['application_management']['websocket_on_violation_port']


        # websockets that outputs on_next notifications for registered constraints / static timeouts
        self.ws_on_next = WebSocketThread("WebSocket onNext", ws_on_next_port, ws_on_next_address)

        # websockets that outputs on_timeout notifications for registered constraints / static timeouts
        self.ws_on_timeout = WebSocketThread("WebSocket onTimeout", ws_on_timeout_port, ws_on_timeout_address)
        #
        # websockets that outputs on_violation notifications for registered constraints / static timeouts
        self.ws_on_violation = WebSocketThread("WebSocket onViolation", ws_on_violation_port, ws_on_violation_address)

        #

    # invokes the on_next callback of the remote object
    def onNext(self, id, key, value, completeness, timeout, timestamp):
        message = {'id': id, 'data_source': key, 'value': value, 'completeness': completeness, 'timeOut': timeout, 'timestamp': timestamp}
        self.ws_on_next.publish(json.dumps(message))

    # invokes the on_timeout callback of the remote object
    def onTimeout(self, id, key, completeness, timeout, timestamp):
        message = {'id': id, 'data_source': key, 'value': None, 'completeness': completeness, 'timeOut': timeout, 'timestamp': timestamp}
        self.ws_on_timeout.publish(json.dumps(message))

    # invokes the on_timeout callback of the remote object
    def onViolation(self, id, key, value, completeness, timeout, timestamp):
        if value != None:
            message = {'id': id, 'data_source': key, 'value': value, 'completeness': completeness, 'timeOut': timeout, 'timestamp': timestamp }
            self.ws_on_violation.publish(json.dumps(message))
        # else due to timeout
        else:
            message = {'id': id, 'data_source': key, 'value': None, 'completeness': completeness, 'timeOut': timeout, 'timestamp': timestamp}
            self.ws_on_violation.publish(json.dumps(message))

