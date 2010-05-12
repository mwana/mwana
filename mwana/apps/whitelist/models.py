from django.db import models

from rapidsms.models import Connection


class TrialPeriod(models.Model):
    connection = models.ForeignKey(Connection, related_name='trial_periods')
    start_date = models.DateTimeField()
    expire_date = models.DateTimeField()
