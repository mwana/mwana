class Alert:

    NOT_SENDING_DBS = 1
    LONG_PENDING_RESULTS = 2

    def __init__(self, type, message):
        self.type = type
        self.message = message

