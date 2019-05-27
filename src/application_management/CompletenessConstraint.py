# Encapsulates a completeness constraint, registered by external application(s).

class CompletenessConstraint:

    def __init__(self, id, pid1, pid2, mac, measurement, constraint, threshold, remoteObject):
        self.id = id
        # pid1/pid2 = peripheral identifier
        self.pid1 = pid1
        self.pid2 = pid2
        # MAC address of the device to which the peripheral is connected.
        self.mac = mac
        # what the peripheral measures, e.g. temperature
        self.measurement = measurement
        # completeness constraint
        self.constraint = constraint
        # application object to be invoked by Updater
        self.remoteObject = remoteObject
        # constraint is satisfied as long as completeness >= constraint, for over self.threshold % of packets.
        self.threshold = float(threshold)


    def getID(self):
        return self.id

    def getThreshold(self):
        return self.threshold

    def getCompleteness(self):
        return self.constraint

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

    def getRemoteObject(self):
        return self.remoteObject

    def sameKey(self, key):
        return self.pid1 + '/' + self.pid2 + ':' + self.mac + '|' + self.measurement == key


