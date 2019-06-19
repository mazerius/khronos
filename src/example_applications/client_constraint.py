##### An example application that registers a completeness constraint for a discovered device to Khronos.

import Pyro4
import datetime
import time
import os
import requests
import threading
import json
import websocket

# create remote object with three methods: on_next and on_timeout
@Pyro4.expose
class Client(object):

    # invoked when packets arrive within predicted timeout.
    # value is the value of the sensor data.
    # timeout is the value of the next timeout.
    # completeness is the value of the currently achieved completeness.
    def on_next(self, value, completeness, timeout, timestamp):
        print(str(datetime.datetime.now()), "on_next with value:", value, ', timeout:', timeout, 'and completeness', completeness, 'at timestamp', timestamp)

    # invoked when timeout occurs before packet arrival.
    # value is the value of the sensor data.
    # timeout is the value of the next timeout.
    # completeness is the value of the currently achieved completeness.
    def on_timeout(self, completeness, timeout, timestamp):
        print(str(datetime.datetime.now()), "on_timeout with timeout:", timeout, ', completeness', completeness, 'at timestamp', timestamp)

    # invoked when constraint is violated. Value is the value of the sensor data (if any).
    # timeout is the value of the next timeout.
    # completeness is the value of the currently achieved completeness.
    def on_violation(self, value, completeness, timeout, timestamp):
        print(str(datetime.datetime.now()), "on_violation with value:", value, ', timeout:', timeout, 'and completeness', completeness, 'at timestamp', timestamp)



uri = ""

# listens for incoming remote method invocations
class ThreadingExample(object):
    """ Threading example class
    The run() method will be started and it will run in the background
    until the application exits.
    """

    def __init__(self, interval=1):
        """ Constructor
        :type interval: int
        :param interval: Check interval, in seconds
        """
        self.interval = interval

        thread = threading.Thread(target=self.run, args=())
        thread.start()

    def run(self):
        """ Method that runs forever """
        while True:
            global uri
            daemon = Pyro4.Daemon()  # make a Pyro daemon
            uri = daemon.register(Client)  # register the greeting maker as a Pyro object
            daemon.requestLoop()


# obtain address and port from config file
os.chdir('..')
with open(os.path.join(os.path.join(os.getcwd(), 'configuration'), 'general_config')) as json_data_file:
    data = json.load(json_data_file)
    khronos_address = data["khronos"]["address"]
    khronos_port = data["khronos"]["port"]

khronos_url = 'http://' + khronos_address + ':' + str(khronos_port)

# starts the thread for RMI
example = ThreadingExample()
# gives the thread time to register the remote object
time.sleep(2)

# discovers available CPS devices, selects arbitrary device for which to register a static timeout.

headers = {'Content-Type' : 'application/json'}
devices = requests.get(khronos_url + '/devices').json()
example_device = json.loads(devices[0])
completeness_constraint = "0.35"

threshold = 0.99999

# parse peripheral id1, peripheral id2, measurement and mac address
pid1 = example_device['id'].split('/')[0]
pid2 = example_device['id'].split('/')[1].split(':')[0]
measurement = example_device['id'].split('|')[1]
mac = example_device['id'].split(':')[1].split('|')[0]

print('Registering Constraint for Discovered Device' + example_device['name'] +  '...')

# registers completeness constraint for selected device to Khronos.
response = requests.put(khronos_url + '/registerCompletenessConstraintRMI' + '/' + pid1 + '/' + pid2 + '/' +mac + '/' + measurement + '/' + completeness_constraint + '/' + str(threshold) + '/'+ uri.asString().strip())
print('ID:', response.text)

