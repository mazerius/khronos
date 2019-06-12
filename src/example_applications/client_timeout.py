##### An example application that registers a static timeout for a discovered device to Khronos.


import Pyro4
import datetime
import time
import requests
import threading
import json
import os


# create remote object with two methods: on_next and on_timeout
@Pyro4.expose
class Client(object):

    # should be invoked when packets arrive within given constraints. Value is the value of the sensor data.
    def on_next(self, value, completeness, timeout):
        print(str(datetime.datetime.now()), "on_next with value:", value, ', timeout:', timeout, 'and completeness', completeness)

    # should be invoked when packets arrive outside given constraints. Value is the value of the sensor data.
    def on_timeout(self, completeness, timeout):
        print(str(datetime.datetime.now()), "on_timeout with timeout:", timeout, ', completeness', completeness)


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
peripheral_id = ""
# static timeout
timeout = 14.5

# parse peripheral id1, peripheral id2, measurement and mac address
pid1 = example_device['id'].split('/')[0]
pid2 = example_device['id'].split('/')[1].split(':')[0]
measurement = example_device['id'].split('|')[1]
mac = example_device['id'].split(':')[1].split('|')[0]

print('Registering Timeout for Discovered Device' + pid1 + '/' + pid2 + ':' + mac + '|' + measurement +  '...' )

# registers static timeout for selected device to Khronos.
response = requests.put(khronos_url + '/registerTimeoutRMI' + '/' + pid1 + '/' + pid2 + '/' + mac + '/' + measurement + '/' + str(timeout) + '/'+ uri.asString().strip())
print('ID:', response.text)