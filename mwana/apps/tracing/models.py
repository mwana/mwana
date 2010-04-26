import datetime

from django.db import models

from rapidsms.models import Contact


class Trace(models.Model):
    contact = models.ForeignKey(Contact, related_name='traces',
                                limit_choices_to={'types__slug': 'patient'})
    date = models.DateField()
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self.date = datetime.datetime.now()
        return super(Trace, self).save(*args, **kwargs)