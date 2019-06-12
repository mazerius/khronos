import math
import datetime



# Represents a sensor data stream from a source in the underlying CPS communication.
class Stream:


    def __init__(self, peripheral_id, device_id, alpha, beta, db, constraints_to_K, window_size):

        self.peripheral_id = peripheral_id
        self.device_id = device_id
        # to initialize atvar
        self.initialized = False
        # maps K to constraints
        self.constraints_to_K = constraints_to_K # K value for each constraint.
        # to check if packet has previously been received.
        self.last_timestamp = -1
        # database instance to write to, if provided
        self.db = db
        self.window_size = window_size # for moving averages.

        # '<constraint>': <timeout>
        self.completeness_to_timeout = dict()
        # '<constraint>' : [0 or 1], depending if packet arrived before timeout.
        self.accuracies_constraints = dict()
        # '<constraint>' : x.y, where x.y the ratio of 1's in self.accuracies_constraints.
        self.moving_average_accuracies_constraints = dict()
        # '<constraint>' : [achieved completeness], used to compute moving average for below_constraint.
        self.moving_average_accuracy_constraints = dict()
        # '<constraint>' : moving average for the ratio of achieved completeness that's above the constraint.
        self.moving_average_achieved_completeness = dict()

        self.moving_average_achieved_completenesses = dict()

        self.above_constraint = dict()

        #self.moving_average_above_constraint = dict()

        # initializing key-value pairs for above parameters per initial constraint
        for constraint in constraints_to_K.keys():
            self.completeness_to_timeout[constraint] = []
            self.accuracies_constraints[constraint] = []
            self.moving_average_accuracy_constraints[constraint] = None
            self.moving_average_accuracies_constraints[constraint] = []
            self.moving_average_achieved_completeness[constraint] = None
            self.moving_average_achieved_completenesses[constraint] = []
            self.above_constraint[constraint] = None


        # '<timeout> : x.y, where x.y the ratio of 1's in self.accuracies_static_timeout.
        self.moving_average_accuracy_timeouts = dict()
        # '<constraint>' : [0 or 1], depending if packet arrived before timeout.
        self.accuracies_static_timeout = dict()

        # prediction technique parameters
        self.alpha = alpha
        self.beta = beta
        self.smoothed_arrival_time = -1
        self.arrival_time_variance = -1
        self.last_arrival_time = -1


    # getters

    def getAchievedCompletenessForConstraints(self):
        return self.moving_average_accuracy_constraints

    def getMovingAverageAchievedCompletenessForConstraints(self):
        return self.moving_average_achieved_completeness

    def getAchievedCompletenessForStaticTimeouts(self):
        return self.moving_average_accuracy_timeouts

    def getAboveConstraintForConstraints(self):
        return self.above_constraint


    # def getBelowConstraintRatioForConstraints(self):
    #     return self.moving_average_moving_average_accuracies

    def getCompletenessConstraintToTimeWindow(self):
        return self.completeness_to_timeout

    def getNextTimeoutsForConstraints(self):
        return self.completeness_to_timeout

    def getTimeoutToAchievedCompleteness(self):
        return self.moving_average_accuracy_timeouts



    # to be called when first packet arrives
    # initializes parameters for timeout prediction algorithm to automatically compute the next timeout.
    def initializePredictionTechnique(self, arrival_time):
        self.smoothed_arrival_time = arrival_time
        arrival_time_variance = float(arrival_time)/2
        self.arrival_time_variance = arrival_time_variance


    # adds accuracy (0 or 1) upon packet arrival for given completeness constraint, storing up to self.window_size entries.
    def addAccuracyForConstraint(self, accuracy, timestamp, constraint):
        if len(self.accuracies_constraints[constraint]) < self.window_size:
            self.accuracies_constraints[constraint].append((accuracy, timestamp))
        else:
            self.accuracies_constraints[constraint] = self.accuracies_constraints[constraint][1:]
            self.accuracies_constraints[constraint].append((accuracy, timestamp))

    # adds accuracy (0 or 1) upon packet arrival for given static timeout, storing up to self.window_size entries.
    def addAccuracyforStaticTimeout(self, accuracy, timestamp, timeout):
        if len(self.accuracies_static_timeout[timeout]) < self.window_size:
            self.accuracies_static_timeout[timeout].append((accuracy, timestamp))
        else:
            self.accuracies_static_timeout[timeout] = self.accuracies_static_timeout[timeout][1:]
            self.accuracies_static_timeout[timeout].append((accuracy, timestamp))

    # adds achieved completeness upon packet arrival for given constraint, storing up to self.window_size entries.
    def addMovingAverageAccuracyForConstraint(self, completeness, ma_accuracy, timestamp):
        if len(self.moving_average_accuracies_constraints[completeness]) < self.window_size:
            self.moving_average_accuracies_constraints[completeness].append((ma_accuracy, timestamp))
        else:
            self.moving_average_accuracies_constraints[completeness] = self.moving_average_accuracies_constraints[completeness][1:]
            self.moving_average_accuracies_constraints[completeness].append((ma_accuracy, timestamp))

    # adds achieved completeness upon packet arrival for given constraint, storing up to self.window_size entries.
    def addMovingAverageAchievedCompleteness(self, completeness, ma_achieved_completeness, timestamp):
        if len(self.moving_average_achieved_completenesses[completeness]) < self.window_size:
            self.moving_average_achieved_completenesses[completeness].append((ma_achieved_completeness, timestamp))
        else:
            self.moving_average_achieved_completenesses[completeness] = self.moving_average_achieved_completenesses[completeness][1:]
            self.moving_average_achieved_completenesses[completeness].append((ma_achieved_completeness, timestamp))


    # # adds achieved completeness upon packet arrival for given constraint, storing up to self.window_size entries.
    # def addMovingAverageAboveConstraint(self, completeness, ma_achieved_completeness, timestamp):
    #     if len(self.moving_average_above_constraint[completeness]) < self.window_size:
    #         self.moving_average_above_constraint[completeness].append((ma_achieved_completeness, timestamp))
    #     else:
    #         self.moving_average_above_constraint[completeness] = self.moving_average_above_constraint[completeness][1:]
    #         self.moving_average_above_constraint[completeness].append((ma_achieved_completeness, timestamp))

    # updates the moving average for achieved completeness for given constraint.
    def updateAchievedCompletenessForConstraint(self, constraint, time_to_write):
        values = []
        timestamps = []
        for ac in self.accuracies_constraints[constraint]:
            values.append(ac[0])
            timestamps.append(ac[1])
        cumsum, moving_aves = [0], []

        for i, x in enumerate(values, 1):
            cumsum.append(cumsum[i - 1] + x)
            if i >= self.window_size:
                moving_ave = (cumsum[i] - cumsum[i - self.window_size]) / self.window_size
                moving_aves.append((moving_ave, timestamps[i - 1]))
        if len(moving_aves) > 0:
            self.moving_average_accuracy_constraints[constraint] = (moving_aves[0][0], time_to_write)

    # updates the moving average for achieved completeness for given static timeout.
    def updateAchievedCompletenessForTimeout(self, timeout, timeToWrite):
        values = []
        timestamps = []
        for ac in self.accuracies_static_timeout[timeout]:
            values.append(ac[0])
            timestamps.append(ac[1])
        cumsum, moving_aves = [0], []

        for i, x in enumerate(values, 1):
            cumsum.append(cumsum[i - 1] + x)
            if i >= self.window_size:
                moving_ave = (cumsum[i] - cumsum[i - self.window_size]) / self.window_size
                moving_aves.append((moving_ave, timestamps[i - 1]))
        if len(moving_aves) > 0:
            self.moving_average_accuracy_timeouts[timeout] = (moving_aves[0][0], timeToWrite)


    # updates the moving average for the ratio for which the achieved completeness is below the constraint.
    def updateMovingAverageAchievedCompleteness(self, constraint):
        values = []
        timestamps = []
        for ac in self.moving_average_accuracies_constraints[constraint]:
            values.append(ac[0])
            timestamps.append(ac[1])
        cumsum, moving_aves = [0], []

        for i, x in enumerate(values, 1):
            cumsum.append(cumsum[i - 1] + x)
            if i >= self.window_size:
                moving_ave = (cumsum[i] - cumsum[i - self.window_size]) / self.window_size
                moving_aves.append((moving_ave, timestamps[i - 1]))
        if len(moving_aves) > 0:
            self.moving_average_achieved_completeness[constraint] = moving_aves[0][0]

    # updates the moving average for the ratio for which the achieved completeness is below the constraint.
    def updateMovingAverageAboveConstraint(self, constraint):
        values = []
        timestamps = []
        for ac in self.moving_average_achieved_completenesses[constraint]:
            if ac[0] >= constraint:
                values.append(1)
            else:
                values.append(0)
            timestamps.append(ac[1])
        cumsum, moving_aves = [0], []

        for i, x in enumerate(values, 1):
            cumsum.append(cumsum[i - 1] + x)
            if i >= self.window_size:
                moving_ave = (cumsum[i] - cumsum[i - self.window_size]) / self.window_size
                moving_aves.append((moving_ave, timestamps[i - 1]))
        if len(moving_aves) > 0:
            self.above_constraint[constraint] = moving_aves[0][0]


    # invoked upon packet arrival to update all statistics and computes next timeout prediction(s)
    def increment(self, timestamp, time_to_write):
        if self.last_timestamp == -1:
            self.last_timestamp = timestamp
            return False
        else:
            # in microseconds
            rat = (timestamp - self.last_timestamp) / 1000000
            self.last_timestamp = timestamp
            result = self.incrementCollection(rat, time_to_write)
            return result

    # called upon whenever a new packet from this peripheral arrives.
    # it then triggers the (re)computation of the pastWindow, and updates self.collection accordingly.
    # returns True when all has been initialized, False otherwise
    def incrementCollection(self, rat, timeToWrite):
            time_received = rat
            if not self.initialized:
                self.initializePredictionTechnique(time_received)
                print(datetime.datetime.now(), '| [Stream]:', self.peripheral_id + ':' + self.device_id,
                      'initialized successfully.')
                self.initialized = True
                # compute next timeouts for each completeness constraint
                for key in self.getCompletenessConstraintToTimeWindow().keys():
                    new_key = key
                    (newTimeWindow, K) = self.computeTimeout(float(new_key))
                    self.completeness_to_timeout[key] = (newTimeWindow, timeToWrite)
                # result not ready to be published yet
                return False
            else:
                self.last_arrival_time = time_received
                self.updateArrivalTimeVariance()
                self.updateSmoothedArrivalTime()
                print(datetime.datetime.now(), '| [Stream]:', self.peripheral_id + ':' + self.device_id,' updated ATVAR, SAT.')
                # compute next timeout for each registered constraint
                for key in self.getCompletenessConstraintToTimeWindow().keys():
                    # for constraints added at runtime that may no yet be initialized
                    if self.completeness_to_timeout[key] == None:
                        (newTimeWindow, K) = self.computeTimeout(float(new_key))
                        self.completeness_to_timeout[key] = (newTimeWindow, timeToWrite)
                    else:
                        new_key = key
                        (newTimeWindow, K) = self.computeTimeout(float(new_key))
                        accuracy = 0
                        if self.completeness_to_timeout[key][0] >= rat:
                            # packet arrived before predicted timeout
                            accuracy = 1
                        self.addAccuracyForConstraint(accuracy, timeToWrite, key)
                        # if enough data has arrived, compute moving averages
                        if len(self.accuracies_constraints[key]) >= self.window_size:
                            self.updateAchievedCompletenessForConstraint(key, timeToWrite)
                            self.addMovingAverageAccuracyForConstraint(key, self.moving_average_accuracy_constraints[key][0], self.moving_average_accuracy_constraints[key][1])
                            # if enough data has arrived, compute moving averages
                            if len(self.moving_average_accuracies_constraints[key]) >= self.window_size:
                                self.updateMovingAverageAchievedCompleteness(key)
                                self.addMovingAverageAchievedCompleteness(key, self.moving_average_achieved_completeness[key], timeToWrite)
                                if len(self.moving_average_achieved_completenesses[key]) >= self.window_size:
                                    self.updateMovingAverageAboveConstraint(key)
                        self.completeness_to_timeout[key] = (newTimeWindow, timeToWrite)
                # update accuracy and achieved completeness for each registered static timeout
                for timeout in self.moving_average_accuracy_timeouts.keys():
                    accuracy = 0
                    if float(timeout) >= rat:
                        accuracy = 1
                    self.addAccuracyforStaticTimeout(accuracy, timeToWrite, timeout)
                    if len(self.accuracies_static_timeout[timeout]) >= self.window_size:
                        self.updateAchievedCompletenessForTimeout(timeout, timeToWrite)
                # data ready to be published
                return True


    def trackCompletenessForTimeout(self, timeout):
        timeout = timeout
        if not (timeout in self.moving_average_accuracy_timeouts.keys()):
            print(datetime.datetime.now(), '| [Stream]:', self.peripheral_id + ':' + self.device_id, 'tracking completeness for static timeout', timeout, 'seconds.')
            self.moving_average_accuracy_timeouts[timeout] = None
            self.accuracies_static_timeout[timeout] = []

    def trackTimeoutForCompleteness(self, constraint):
        constraint = float(constraint)
        if not (constraint in self.completeness_to_timeout.keys()):
            print(datetime.datetime.now(), '| [Stream]:', self.peripheral_id + ':' + self.device_id, 'tracking timeout for completeness constraint', constraint, 'seconds.')
            self.completeness_to_timeout[constraint] = None
            self.constraints_to_K[constraint] = (self.constraints_to_K[math.floor(10 * constraint) / 10] + self.constraints_to_K[math.ceil(10 * constraint) / 10]) / 2
            self.accuracies_constraints[constraint] = []
            self.moving_average_accuracy_constraints[constraint] = None
            self.moving_average_accuracies_constraints[constraint] = []
            self.moving_average_achieved_completenesses[constraint] = []
            self.moving_average_achieved_completeness[constraint] = None

            self.above_constraint[constraint] = None


    # computes the next timeout for given constraint
    def computeTimeout(self, constraint):
        #print(datetime.datetime.now(), '| [Stream]:', self.peripheral_id + ':' + self.device_id, 'computing next timeout for constraint.', constraint)
        new_timeout = round(self.smoothed_arrival_time + self.constraints_to_K[constraint] * self.arrival_time_variance,3)
        return (new_timeout, self.constraints_to_K[constraint])

    # updates SAT
    def updateSmoothedArrivalTime(self):
        smoothed_arrival_time = round(self.alpha * self.smoothed_arrival_time + (1 - self.alpha) * self.last_arrival_time, 2)
        self.smoothed_arrival_time = smoothed_arrival_time

    # updates ATVAR
    def updateArrivalTimeVariance(self):
        arrival_time_variance = round(self.beta * self.arrival_time_variance + (1 - self.beta) * abs(
            self.smoothed_arrival_time - self.last_arrival_time), 2)
        self.arrival_time_variance = arrival_time_variance


