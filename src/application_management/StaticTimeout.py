# Encapsualtes a static timeout, registered by external application(s).

class StaticTimeout:

    def __init__(self, id, pid1, pid2, mac, measurement, timeout, remoteObject):
        self.id = id
        # pid1/pid2 = peripheral identifier
        self.pid1 = pid1
        self.pid2 = pid2
        # MAC address of the device to which the peripheral is connected.
        self.mac = mac
        # what the peripheral measures, e.g. temperature
        self.measurement = measurement
        # static timeout
        self.timeout = timeout
        # application object to be invoked by Updater
        self.remoteObject = remoteObject



    def getID(self):
        return self.id

    def getTimeout(self):
        return self.timeout

    def getMeasurement(self):
        return self.measurement

    def getMAC(self):
        return self.mac

    def getPID1(self):
        return self.pid1

    def getPID2(self):
        return self.pid2

    def getDeviceKey(self):
        return self.pid1 + '/' + self.pid2 + ':' + self.mac + '|' + self.measurement

    def sameKey(self, key):
        return self.pid1 + '/' + self.pid2 + ':' + self.mac + '|' + self.measurement == key

    def getRemoteObject(self):
        return self.remoteObject
