# represents a discovered device in the CPS

import json

class DataSource:

    # currently only supports unary/binary operations.
    def __init__(self, id, name, datatype, unit):
        self.id = id
        self.name = name
        self.datatype = datatype
        self.unit = unit

    def __repr__(self):
        return "<Publisher id:%s name:%s datatype:%s unit:%s>" % (self.id, self.name, self.datatype, self.unit)


    def getID(self):
        return self.id

    def setID(self,id):
        self.id = id

    def getName(self):
        return self.name

    def getDataType(self):
        return self.datatype

    def getUnit(self):
        return self.unit

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True)

