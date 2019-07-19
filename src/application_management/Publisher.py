# responsible for publishing events on websockets, when instructed by the Scheduler.
import json


class Publisher:

    def __init__(self):
        self.ws_list = []


    def addWebSocket(self, ws):
        self.ws_list.append(ws)

    def broadcast(self, message):
        for ws in self.ws_list:
            if not ws.closed:
                ws.send(json.dumps(message))
            else:
                # Remove ws if connection closed.
                self.ws_list.remove(ws)


    # invokes the on_next callback of the remote object
    def onNext(self, id, key, value, completeness, timeout, timestamp):
        message = {'id': id, 'data_source': key, 'value': value, 'completeness': completeness, 'timeOut': timeout, 'timestamp': timestamp, 'type': "next"}
        self.broadcast(message)


    # invokes the on_timeout callback of the remote object
    def onTimeout(self, id, key, completeness, timeout, timestamp):
        message = {'id': id, 'data_source': key, 'value': None, 'completeness': completeness, 'timeOut': timeout, 'timestamp': timestamp, 'type': "timeout"}
        self.broadcast(message)

    # invokes the on_timeout callback of the remote object
    def onViolation(self, id, key, value, completeness, timeout, timestamp):
        if value != None:
            message = {'id': id, 'data_source': key, 'value': value, 'completeness': completeness, 'timeOut': timeout, 'timestamp': timestamp, 'type': "violation" }
            self.broadcast(message)

        # else due to timeout
        else:
            message = {'id': id, 'data_source': key, 'value': None, 'completeness': completeness, 'timeOut': timeout, 'timestamp': timestamp, 'type': "violation"}
            self.broadcast(message)

