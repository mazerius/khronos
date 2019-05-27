
from influxdb import InfluxDBClient
import datetime
import pytz
from dateutil import tz
import json
import os


# convert timestamp to local timezone before writing to InfluxDB
from_zone = tz.tzutc()
to_zone = tz.tzlocal()
LOCAL_TIMEZONE = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo


# Responsible for writing data to an influxdb instance.
class InfluxDBWriter:

    def __init__(self, config_path):
        # Load configs
        with open(os.path.join(config_path, 'db_config'))as json_data_file:
            data = json.load(json_data_file)
            self.influxdb_addr = data['influxdb_addr']
            self.influxdb_port = data['influxdb_port']
            self.influxdb_database = data['influxdb_database']
            self.influxdb_username = data['influxdb_username']
            self.influxdb_password = data['influxdb_password']
            self.dbclient = InfluxDBClient(self.influxdb_addr, self.influxdb_port, self.influxdb_username, self.influxdb_password, self.influxdb_database)

    # writes timeout for completeness constraint to DB
    def writePredictedTimeout(self, arrival_time, address, identifier, completeness, value):
        arrival_time = arrival_time.astimezone(pytz.utc)
        arrival_time = arrival_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        try:
            # Convert the string to a float so that it is stored as a number and not a string in the storage
            val = float(value)
            is_float_value = True
        except:
            is_float_value = False

        if is_float_value:
            json_body = [
                {
                    "measurement": "Timeout",
                    "tags": {
                        "mote": address,
                        "peripheral": identifier,
                        "completeness": completeness
                    },
                    "time": arrival_time,
                    "fields": {
                        "value": val
                    }
                }
            ]
            self.dbclient.write_points(json_body)

    # writes achieved completeness for completeness constraint to DB
    def writeAchievedCompletenessForConstraint(self, arrival_time, device_address, identifier, constraint, ma):
        try:
            # Convert the string to a float so that it is stored as a number and not a string in the storage
            val = float(ma)
            is_float_value = True
        except:
            is_float_value = False

        if is_float_value:
            json_body = [
                {
                    "measurement": "Achieved_Completeness",
                    "tags": {
                        "mote": device_address,
                        "peripheral": identifier,
                        "constraint": constraint
                    },
                    "time": arrival_time,
                    "fields": {
                        "value": val
                    }
                }
            ]
            self.dbclient.write_points(json_body)



    def writePredictionError(self, arrival_time, device_address, identifier, constraint, pe):
        try:
            # Convert the string to a float so that it is stored as a number and not a string in the storage
            val = float(pe)
            is_float_value = True
        except:
            is_float_value = False

        if is_float_value:
            json_body = [
                {
                    "measurement": "Prediction_Error",
                    "tags": {
                        "mote": device_address,
                        "peripheral": identifier,
                        "constraint": constraint
                    },
                    "time": arrival_time,
                    "fields": {
                        "value": val
                    }
                }
            ]
            self.dbclient.write_points(json_body)

    def writeATVARToDatabase(self, arrival_time, device_address, identifier, atvar):
        try:
            # Convert the string to a float so that it is stored as a number and not a string in the storage
            val = float(atvar)
            isfloatValue = True
        except:
            isfloatValue = False

        if isfloatValue:
            json_body = [
                {
                    "measurement": "Arrival_Time_Variance",
                    "tags": {
                        "mote": device_address,
                        "peripheral": identifier,
                    },
                    "time": arrival_time,
                    "fields": {
                        "value": val
                    }
                }
            ]
            self.dbclient.write_points(json_body)

    def writeSATToDatabase(self, arrival_time, device_address, identifier, sat):
        try:
            # Convert the string to a float so that it is stored as a number and not a string in the storage
            val = float(sat)
            isfloatValue = True
        except:
            isfloatValue = False

        if isfloatValue:
            json_body = [
                {
                    "measurement": "Smoothed_Arrival_Time",
                    "tags": {
                        "mote": device_address,
                        "peripheral": identifier,
                    },
                    "time": arrival_time,
                    "fields": {
                        "value": val
                    }
                }
            ]
            self.dbclient.write_points(json_body)


    def writeAccuracy(self, arrival_time, address, identifier, constraint, value):
        try:
            # Convert the string to a float so that it is stored as a number and not a string in the storage
            val = float(value)
            isfloatValue = True
        except:
            isfloatValue = False
        if isfloatValue:
            json_body = [
                {
                    "measurement": "Accuracy_for_Constraint",
                    "tags": {
                        "mote": address,
                        "peripheral": identifier,
                        "constraint": constraint
                    },
                    "time": arrival_time,
                    "fields": {
                        "value": val
                    }
                }
            ]
            self.dbclient.write_points(json_body)

    def writeAccuracyForStaticTimeout(self, arrival_time, address, identifier, constraint, value):
        try:
            # Convert the string to a float so that it is stored as a number and not a string in the storage
            val = float(value)
            isfloatValue = True
        except:
            isfloatValue = False
        if isfloatValue:
            json_body = [
                {
                    "measurement": "Accuracy_for_Static_Timeout",
                    "tags": {
                        "mote": address,
                        "peripheral": identifier,
                        "constraint": constraint
                    },
                    "time": arrival_time,
                    "fields": {
                        "value": val
                    }
                }
            ]
            self.dbclient.write_points(json_body)

    def writeBelowConstraint(self, arrival_time, address, identifier, constraint, value):
        try:
            # Convert the string to a float so that it is stored as a number and not a string in the storage
            val = float(value)
            isfloatValue = True
        except:
            isfloatValue = False

        if isfloatValue:
            json_body = [
                {
                    "measurement": "Below_Constraint",
                    "tags": {
                        "mote": address,
                        "peripheral": identifier,
                        "constraint": constraint
                    },
                    "time": arrival_time,
                    "fields": {
                        "value": val
                    }
                }
            ]
            self.dbclient.write_points(json_body)


