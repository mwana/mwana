from django.db import models
from rapidsms.models import Contact
from rapidsms.contrib.locations.models import Location
import datetime
# Create your models here.

class TrainingSession(models.Model):
    start_date = models.DateTimeField(default=datetime.datetime.utcnow)
    end_date = models.DateTimeField(blank=True, null=True)
    trainer = models.ForeignKey(Contact)
    is_on = models.BooleanField(default=True)
    location = models.ForeignKey(Location)

    def __unicode__(self):
        return 'Training on %s by %s at %s' % (self.start_date, self.trainer, self.location)
