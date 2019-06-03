from multiprocessing import Process
import time
from src.application_management.CompletenessConstraint import CompletenessConstraint
from src.application_management.StaticTimeout import StaticTimeout
import datetime

# invoked when a process times out, associated with an individual packet arrival
def onTimeout(remoteObject, timeout, completeness, updater):
    time.sleep(float(timeout))
    print(datetime.datetime.now(), '| [Scheduler]:', 'Timeout occurred prior packet arrival. Invoking onTimeout() on Updater.')
    updater.onTimeout(remoteObject, timeout, completeness)

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


    def getUpdater(self):
        return self.updater

    def getDataParser(self):
        return self.data_parser

    # register completeness constraint for device key
    def registerCompleteness(self, device, pid1, pid2, measurement, remote_object, completeness_constraint, threshold):
        constraint = CompletenessConstraint(self.constraint_counter, pid1, pid2, device, measurement, completeness_constraint, threshold, remote_object)
        self.constraints.append(constraint)
        self.constraint_to_process[self.constraint_counter] = None
        key = pid1 + '/' + pid2 + ':' + device + '|' + measurement
        self.network_monitor.trackCompletenessConstraintForStream(key, completeness_constraint)
        self.network_monitor.activatePublisher(key)
        self.constraint_counter += 1

    # register static timeout for device key
    def registerTimeOut(self, device, pid1, pid2, measurement, remote_object, timeout):
        static_timeout = StaticTimeout(self.static_timeout_counter, pid1, pid2, device, measurement, timeout, remote_object)
        key = pid1 + '/' + pid2 + ':' + device + '|' + measurement
        self.timeouts.append(static_timeout)
        self.timeout_to_process[self.static_timeout_counter] = None
        self.network_monitor.trackStaticTimeoutForStream(key, timeout)
        self.network_monitor.activatePublisher(key)
        self.static_timeout_counter += 1




    # when timeout has occured, the scheduler waits for the next packet arrival before restarting a new timeout process.
    def receiveData(self, arrivalTime, timeGenerated, key, value, next_timeout, achieved_completeness_constraints, below_constraint, achieved_completeness_timeouts):
        print(datetime.datetime.now(), '| [Scheduler]:', 'received data from:', key, ', at', arrivalTime, ' with timestamp', timeGenerated)
        # check registered completeness constraints that are linked to received device data
        for constraint in self.constraints:
            if constraint.sameKey(key):
                print(datetime.datetime.now(), '| [Scheduler]:', 'ApplicationConstraint', constraint.getDeviceKey())
                process = self.constraint_to_process[constraint.id]
                if process != None:
                    if process.is_alive():
                        print(datetime.datetime.now(), '| [Scheduler]: packet received prior timeout. Terminating timeout Process.')
                        self.constraint_to_process[constraint.id].terminate()
                        # check if violation
                        print(datetime.datetime.now(), '| [Scheduler]:', 'below_constraint[', constraint.getCompleteness(), ']:', below_constraint[constraint.getCompleteness()])
                        if below_constraint[constraint.getCompleteness()] != None:
                            if below_constraint[constraint.getCompleteness()] < constraint.getThreshold():
                                print(datetime.datetime.now(), '| [Scheduler]: constraint violation detected. Invoking onViolation() on Updater.')
                                self.updater.onViolation(constraint.getRemoteObject(), value, next_timeout[constraint.getCompleteness()], achieved_completeness_constraints[constraint.getCompleteness()])
                            else:
                                print(datetime.datetime.now(), '| [Scheduler]: constraint satisfaction. Invoking onNext() on Updater.')
                                self.updater.onNext(constraint.getRemoteObject(), value, next_timeout[constraint.getCompleteness()], achieved_completeness_constraints[constraint.getCompleteness()])

                else:
                    print(datetime.datetime.now(), '| [Scheduler]: constraint satisfaction. Invoking onNext() on Updater.')
                    self.updater.onNext(constraint.getRemoteObject(), value,
                                        next_timeout[constraint.getCompleteness()],
                                        achieved_completeness_constraints[constraint.getCompleteness()])
                completeness = constraint.getCompleteness()
                print(datetime.datetime.now(), '| [Scheduler]: Initiating new timeout Process with a timeout of', next_timeout[completeness], 'seconds.')
                p = Process(target=onTimeout, args=(constraint.getRemoteObject(), next_timeout[completeness],
                                                achieved_completeness_constraints[completeness],
                                                self.updater))
                self.constraint_to_process[constraint.id] = p
                p.start()



        # check registered static timeouts that are linked to received device data
        for st in self.timeouts:
            if st.sameKey(key):
                print(datetime.datetime.now(), '| [Scheduler]:', 'StaticTimeout', st.getDeviceKey())
                process = self.timeout_to_process[st.id]
                if process != None:
                    # if timeout hasn't occured yet, stop timer and call on_next
                    if process.is_alive():
                        print(datetime.datetime.now(), '| [Scheduler]: packet received prior timeout. Terminating timeout Process.')
                        self.timeout_to_process[st.id].terminate()
                        print(datetime.datetime.now(), '| [Scheduler]: Invoking onNext() on Updater.')
                        self.updater.onNext(st.getRemoteObject(), value,
                                            st.getTimeout(),
                                            achieved_completeness_timeouts[st.getTimeout()])
                else:
                    # first packet arrival, no process yet
                    print(datetime.datetime.now(), '| [Scheduler]: Invoking onNext() on Updater.')
                    self.updater.onNext(st.getRemoteObject(), value,
                                        st.getTimeout(),
                                        achieved_completeness_timeouts[st.getTimeout()])
                print(datetime.datetime.now(), '| [Scheduler]: Initiating new timeout Process with a timeout of', st.getTimeout(), 'seconds.')
                p = Process(target=onTimeout, args=(st.getRemoteObject(), st.getTimeout(), achieved_completeness_timeouts[st.getTimeout()], self.updater))
                self.timeout_to_process[st.id] = p
                p.start()






