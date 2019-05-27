# responsible for invoking the callbacks of application remote objects, when instructed by the Scheduler.

class Updater:

    def __init__(self):
        pass

    # invokes the on_next callback of the remote object
    def onNext(self, remote_object, value, completeness, timeout):
        action = remote_object.on_next
        action(value, completeness, timeout)

    # invokes the on_timeout callback of the remote object
    def onTimeout(self, remote_object, completeness, timeout):
        action = remote_object.on_timeout
        action(completeness, timeout)

    # invokes the on_timeout callback of the remote object
    def onViolation(self, remote_object, value, completeness, timeout):
        action = remote_object.on_violation
        # if packet arrival
        if value != None:
            action(value, completeness, timeout)
        # else due to timeout
        else:
            action(None, completeness, timeout)

