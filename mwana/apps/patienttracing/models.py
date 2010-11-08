import datetime

from django.db import models
from rapidsms.models import Contact

STATUS_CHOICES = (
                  ("N", "new"),
                  ("T", "told"),
                  ("C", "confirmed"),
                  )

class PatientTrace(models.Model):
    
    name = models.CharField(max_length=50) # name of patient to trace
    patient = models.ForeignKey(Contact, related_name='patient_traces',
                                limit_choices_to={'types__slug': 'patient'},
                                null=True, blank=True) # for probable future use
    cba = models.ForeignKey(Contact,
                            limit_choices_to={'types__slug': 'cba'})#cba tells sees patient
    status = models.CharField(choices=STATUS_CHOICES, max_length=1)
    start_date = models.DateTimeField()
    sent_date = models.DateTimeField(null=True, blank=True)
    confirmed_date = models.DateTimeField(null=True, blank=True)
    initiated_by = models.ForeignKey(Contact, related_name='patients_traced',
                                     limit_choices_to={'types__slug': 'clinic_worker'})

    def save(self, * args, ** kwargs):
        if not self.pk:
            self.start_date = datetime.datetime.now()
        super(PatientTrace, self).save(*args, ** kwargs)

