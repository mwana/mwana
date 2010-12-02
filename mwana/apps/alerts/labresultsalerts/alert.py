# vim: ai ts=4 sts=4 et sw=4
class Alert:

    DISTRICT_NOT_SENDING_DBS = 1
    LONG_PENDING_RESULTS = 2
    CLINIC_NOT_USING_SYSTEM = 3
    LAB_NOT_PROCESSING_DBS = 4
    LAB_NOT_SENDING_PAYLOD = 5
    HIGH_LEVEL = 2
    LOW_LEVEL = 1

    def __init__(self, type, message, culprit=None, days_late=None,
                 sort_field=None, level=None, extra=None):
        self.type = type
        self.message = message
        self.sort_field = sort_field
        self.culprit = culprit
        self.days_late = days_late
        self.level = level
        self.extra = extra

    def __getitem__(self, position):
        return (self.type,
                self.message,
                self.culprit,
                self.days_late,
                self.sort_field,
                self.level,
                self.extra
                )[position-1]

