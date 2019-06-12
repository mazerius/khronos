# Encapsualtes a static timeout, registered by external application(s).
from src.application_management.ApplicationRequirement import *

class StaticTimeout(ApplicationRequirement):

    def __init__(self, id, pid1, pid2, mac, measurement, timeout, remoteObject):
        ApplicationRequirement.__init__(self, id,pid1,pid2,mac,measurement, remoteObject)
        # static timeout
        self.timeout = timeout

    def getTimeout(self):
        return self.timeout
