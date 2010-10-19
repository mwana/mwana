class Alert:

    DISTRICT_NOT_SENDING_DBS = 1
    LONG_PENDING_RESULTS = 2
    CLINIC_NOT_USING_SYSTEM = 3
    LAB_NOT_PROCESSING_DBS = 4
    LAB_NOT_SENDING_PAYLOD = 5

    def __init__(self, type, message):
        self.type = type
        self.message = message

