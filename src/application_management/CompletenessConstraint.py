# Encapsulates a completeness constraint, registered by external application(s).
from src.application_management.ApplicationRequirement import *

class CompletenessConstraint(ApplicationRequirement):

    def __init__(self, id, pid1, pid2, mac, measurement, constraint, threshold, remoteObject):
        ApplicationRequirement.__init__(self, id, pid1, pid2, mac, measurement, remoteObject)
        # completeness constraint
        self.constraint = constraint
        # constraint is satisfied as long as completeness >= constraint, for over self.threshold % of packets.
        self.threshold = float(threshold)

    def getThreshold(self):
        return self.threshold

    def getCompleteness(self):
        return self.constraint

