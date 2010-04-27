import datetime

from django.db import models

from rapidsms.models import Contact


class Trace(models.Model):
    patient = models.ForeignKey(Contact, related_name='traces_patient',
                                limit_choices_to={'types__slug': 'patient'})
    worker = models.ForeignKey(Contact, related_name='traces_worker',
                               limit_choices_to={'types__slug': 'patient'})
    date = models.DateField()
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self.date = datetime.datetime.now()
        return super(Trace, self).save(*args, **kwargs)