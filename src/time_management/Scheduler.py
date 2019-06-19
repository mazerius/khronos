import datetime
import time
from multiprocessing import Process
import json
from src.application_management.CompletenessConstraint import CompletenessConstraint

from src.application_management.StaticTimeout import StaticTimeout

from src.application_management.Publisher import Publisher

# invoked when a process times out, associated with an individual packet arrival
# requirement is a static timeout or constraint
#TODO: add onViolation if below constraint != None and < constraint.getThreshold()
#TODO: requirement make superclass
def onTimeout(requirement, completeness,  timeout, timestamp, updater, publisher, below_constraint = None):
    time.sleep(float(timeout))
    print(datetime.datetime.now(), '| [Scheduler]:', 'Timeout occurred prior packet arrival. Invoking onTimeout() on Updater.')
    if below_constraint != None and below_constraint[requirement.getCompleteness()] != None:
        if below_constraint[requirement.getCompleteness()] < requirement.getThreshold():
            if requirement.getRemoteObject() != None:
                updater.onViolation(requirement.getRemoteObject(), completeness, timeout, timestamp)
            else:
                publisher.onViolation(requirement.getID(), requirement.getDeviceKey(), None, completeness, timeout, timestamp)
        else:
            if requirement.getRemoteObject() != None:
                updater.onTimeout(requirement.getRemoteObject(), completeness, timeout, timestamp)
            else:
                publisher.onTimeout(requirement.getID(), requirement.getDeviceKey(), completeness, timeout, timestamp)
    else:
        if requirement.getRemoteObject() != None:
            updater.onTimeout(requirement.getRemoteObject(), completeness, timeout, timestamp)
        else:
            publisher.onTimeout(requirement.getID(), requirement.getDeviceKey(), completeness, timeout, timestamp)

# Responsible for coordinating callback methods of (remote) application objects,
# based on packet arrival times and timeouts.
class Scheduler:

    # used for unique IDs of ApplicationConstraint objects.
    # both an ApplicationConstraint and the corresponding Process share the same ID.
    constraint_counter = 0
    # used for unique IDs of StaticTimeout objects.
    # both a StaticTimeout and the corresponding Process share the same ID.
    static_timeout_counter = 0

    def __init__(self, updater, data_parser, network_monitor):
        self.updater = updater
        self.publisher = Publisher()
        self.data_parser = data_parser
        self.data_parser.setScheduler(self)
        self.network_monitor = network_monitor
        self.constraints = []
        # ApplicationConstraint.id : process
        self.constraint_to_process = dict()
        # static timeouts
        self.timeouts = []
        # StaticTimeout.id : process
        self.timeout_to_process = dict()
        # used to determine ID of registered constraints / static timeouts.
        self.registration_id = 0


    def getUpdater(self):
        return self.updater

    def getDataParser(self):
        return self.data_parser

    # register completeness constraint for device key
    # returns unique ID to identify websocket notifications for this registration
    def registerCompleteness(self, device, pid1, pid2, measurement, completeness_constraint, threshold, remote_object=None):
        constraint = CompletenessConstraint(self.registration_id, pid1, pid2, device, measurement, completeness_constraint, threshold, remote_object)
        self.constraints.append(constraint)
        self.constraint_to_process[self.registration_id] = None
        key = pid1 + '/' + pid2 + ':' + device + '|' + measurement
        self.network_monitor.trackCompletenessConstraintForStream(key, completeness_constraint)
        self.network_monitor.activateDataSource(key)
        #self.constraint_counter += 1
        self.registration_id +=1
        return self.registration_id - 1

    # register static timeout for device key
    # returns unique ID to identify websocket notifications for this registration
    def registerTimeOut(self, device, pid1, pid2, measurement, timeout, remote_object=None):
        static_timeout = StaticTimeout(self.registration_id, pid1, pid2, device, measurement, timeout, remote_object)
        key = pid1 + '/' + pid2 + ':' + device + '|' + measurement
        self.timeouts.append(static_timeout)
        self.timeout_to_process[self.registration_id] = None
        self.network_monitor.trackStaticTimeoutForStream(key, timeout)
        self.network_monitor.activateDataSource(key)
        #self.static_timeout_counter += 1
        self.registration_id +=1
        return self.registration_id - 1



    # when timeout has occured, the scheduler waits for the next packet arrival before restarting a new timeout process.
    def receiveData(self, arrival_time, timeGenerated, key, value, next_timeout, achieved_completeness_constraints, above_constraint, achieved_completeness_timeouts, timestamp):
        print(datetime.datetime.now(), '| [Scheduler]:', 'Received data from:', key, ', at', arrival_time, ' with timestamp generated', timeGenerated)
        # check registered completeness constraints that are linked to received device data
        for constraint in self.constraints:
            if constraint.sameKey(key):
                print(datetime.datetime.now(), '| [Scheduler]:', 'ApplicationConstraint', constraint.getDeviceKey())
                process = self.constraint_to_process[constraint.getID()]
                if process != None:
                    if process.is_alive():
                        print(datetime.datetime.now(), '| [Scheduler]: packet received prior timeout. Terminating timeout Process.')
                        self.constraint_to_process[constraint.getID()].terminate()
                        # check if violation
                        if above_constraint[constraint.getCompleteness()] != None:
                            if above_constraint[constraint.getCompleteness()] < constraint.getThreshold():
                                if constraint.getRemoteObject() != None:
                                    print(datetime.datetime.now(),
                                          '| [Scheduler]: constraint violation detected. Invoking onViolation() on Updater.')
                                    self.updater.onViolation(constraint.getRemoteObject(), value, achieved_completeness_constraints[constraint.getCompleteness()], next_timeout[constraint.getCompleteness()], timestamp)
                                else:
                                    print(datetime.datetime.now(),
                                          '| [Scheduler]: constraint violation detected. Invoking onViolation() on Publisher.')
                                    self.publisher.onViolation(constraint.getID(), key, value, achieved_completeness_constraints[constraint.getCompleteness()],  next_timeout[constraint.getCompleteness()], timestamp)
                            else:
                                if constraint.getRemoteObject() != None:
                                    print(datetime.datetime.now(),
                                          '| [Scheduler]: constraint satisfaction. Invoking onNext() on Updater.')
                                    self.updater.onNext(constraint.getRemoteObject(), value, achieved_completeness_constraints[constraint.getCompleteness()],next_timeout[constraint.getCompleteness()], timestamp)
                                else:
                                    print(datetime.datetime.now(),
                                          '| [Scheduler]: constraint satisfaction. Invoking onNext() on Publisher.')
                                    self.publisher.onNext(constraint.getID(), key, value, achieved_completeness_constraints[constraint.getCompleteness()], next_timeout[constraint.getCompleteness()], timestamp)
                        else:
                            if constraint.getRemoteObject() != None:
                                print(datetime.datetime.now(),
                                      '| [Scheduler]: constraint satisfaction. Invoking onNext() on Updater.')
                                self.updater.onNext(constraint.getRemoteObject(), value,
                                                    achieved_completeness_constraints[constraint.getCompleteness()],
                                                    next_timeout[constraint.getCompleteness()], timestamp)
                            else:
                                print(datetime.datetime.now(),
                                      '| [Scheduler]: constraint satisfaction. Invoking onNext() on Publisher.')
                                self.publisher.onNext(constraint.getID(), key, value,
                                                      achieved_completeness_constraints[constraint.getCompleteness()],
                                                      next_timeout[constraint.getCompleteness()], timestamp)
                else:
                    if constraint.getRemoteObject() != None:
                        print(datetime.datetime.now(),
                              '| [Scheduler]: constraint satisfaction. Invoking onNext() on Updater.')
                        print('next timeout',next_timeout[constraint.getCompleteness()])
                        self.updater.onNext(constraint.getRemoteObject(), value,
                                        achieved_completeness_constraints[constraint.getCompleteness()],
                                        next_timeout[constraint.getCompleteness()], timestamp)
                    else:
                        print(datetime.datetime.now(),
                              '| [Scheduler]: constraint satisfaction. Invoking onNext() on Publisher.')

                        self.publisher.onNext(constraint.getID(), key, value,
                                          achieved_completeness_constraints[constraint.getCompleteness()], next_timeout[constraint.getCompleteness()], timestamp)

                completeness = constraint.getCompleteness()
                print(datetime.datetime.now(), '| [Scheduler]: Initiating new timeout Process with a timeout of', next_timeout[completeness], 'seconds.')
                p = Process(target=onTimeout, args=(constraint,
                                                    achieved_completeness_constraints[completeness], next_timeout[completeness], timestamp,
                                                    self.updater, self.publisher, above_constraint))
                self.constraint_to_process[constraint.getID()] = p
                p.start()



        # check registered static timeouts that are linked to received device data
        for st in self.timeouts:
            if st.sameKey(key):
                print(datetime.datetime.now(), '| [Scheduler]:', 'StaticTimeout', st.getDeviceKey())
                process = self.timeout_to_process[st.getID()]
                if process != None:
                    # if timeout hasn't occured yet, stop timer and call on_next
                    if process.is_alive():
                        print(datetime.datetime.now(), '| [Scheduler]: packet received prior timeout. Terminating timeout Process.')
                        self.timeout_to_process[st.getID()].terminate()
                        if st.getRemoteObject() != None:
                            print(datetime.datetime.now(), '| [Scheduler]: Invoking onNext() on Updater.')
                            self.updater.onNext(st.getRemoteObject(), value,
                                            achieved_completeness_timeouts[st.getTimeout()],
                                            float(st.getTimeout()), timestamp)
                        else:
                            print(datetime.datetime.now(), '| [Scheduler]: Invoking onNext() on Publisher.')
                            self.publisher.onNext(st.getID(), key, value,
                                              achieved_completeness_timeouts[st.getTimeout()],  float(st.getTimeout()), timestamp)

                else:
                    # first packet arrival, no process yet
                    if st.getRemoteObject()!=None:
                        print(datetime.datetime.now(), '| [Scheduler]: Invoking onNext() on Updater.')
                        self.updater.onNext(st.getRemoteObject(), value,
                                        achieved_completeness_timeouts[st.getTimeout()],
                                        float(st.getTimeout()), timestamp)
                    else:
                        print(datetime.datetime.now(), '| [Scheduler]: Invoking onNext() on Publisher.')
                        self.publisher.onNext(st.getID(), key, value,
                                          achieved_completeness_timeouts[st.getTimeout()], float(st.getTimeout()),timestamp)

                print(datetime.datetime.now(), '| [Scheduler]: Initiating new timeout Process with a timeout of', st.getTimeout(), 'seconds.')
                p = Process(target=onTimeout, args=(st, achieved_completeness_timeouts[st.getTimeout()], float(st.getTimeout()), timestamp, self.updater, self.publisher))
                self.timeout_to_process[st.getID()] = p
                p.start()






