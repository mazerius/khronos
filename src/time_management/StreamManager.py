
import datetime

from src.time_management.Stream import Stream


# Manages Stream objects for sensor data sources in the CPS infrastructure.
class StreamManager:


    def __init__(self, influxdb_client=None):
        self.streams = list()
        self.influxdb_client = influxdb_client


    def getStreams(self):
        return self.streams


    def createStream(self, peripheral_id, device_id, alpha, beta, influxdb_client, constraints_to_K, window_size):
        print(datetime.datetime.now(), '| [StreamManager]: creating Stream for', peripheral_id + ':' + device_id)
        stream = Stream(peripheral_id, device_id, alpha, beta, influxdb_client, constraints_to_K, window_size)
        self.streams.append(stream)


    def getStreamByID(self, peripheral_id, device_id):
        for stream in self.streams:
            if stream.peripheral_id == peripheral_id and stream.device_id == device_id:
                return stream
        return None


    def streamExists(self, peripheral_id, device_id):
        for stream in self.streams:
            if stream.peripheral_id == peripheral_id and stream.device_id == device_id:
                return True
        return False

    # track Completeness values for static imeout
    def trackStaticTimeout(self, peripheral_id, device_id, timeout):
        print(datetime.datetime.now(), '| [StreamManager]: tracking completeness for static timeout for', peripheral_id + ':' + device_id, 'with value', timeout)
        stream = self.getStreamByID(peripheral_id, device_id)
        stream.trackCompletenessForTimeout(timeout)

    # track TimeWindow values for given completeness constraint
    def trackCompletenessConstraint(self, peripheral_id, device_id, constraint):
        print(datetime.datetime.now(), '| [StreamManager]: tracking timeout for completeness constraint for', peripheral_id + ':' + device_id, 'with value', constraint)
        stream = self.getStreamByID(peripheral_id, device_id)
        stream.trackTimeoutForCompleteness(constraint)

