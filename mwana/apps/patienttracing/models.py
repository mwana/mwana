import datetime

from django.db import models
from rapidsms.models import Contact

STATUS_CHOICES = (
                  ("N", "new"),
                  ("T", "told"),
                  ("C", "confirmed"),
                  ("L", "lost to followup"),# when mother can't be traced
                  )

class PatientTrace(models.Model):
    # person who initiates the tracing
    initiator = models.ForeignKey(Contact, related_name='patients_traced',
                                     limit_choices_to={'types__slug': 'clinic_worker'})
    name = models.CharField(max_length=50) # name of patient to trace
    patient = models.ForeignKey(Contact, related_name='patient_traces',
                                limit_choices_to={'types__slug': 'patient'},
                                null=True, blank=True) # for probable future use
    messenger = models.ForeignKey(Contact,  related_name='patients_reminded',
                            limit_choices_to={'types__slug': 'cba'})# cba who informs patient

    confirmed_by = models.ForeignKey(Contact, related_name='patient_traces_confirmed',
                            limit_choices_to={'types__slug': 'cba'})# cba who confirms that patient visited clinic

    status = models.CharField(choices=STATUS_CHOICES, max_length=1) # status of tracing activity  

    start_date = models.DateTimeField() # date when tracing starts
    reminded_on = models.DateTimeField() # date when cba tells mother
    confirmed_date = models.DateTimeField(null=True, blank=True)# date of confirmation that patient visited clinic   
    

    def save(self, * args, ** kwargs):
        if not self.pk:
            self.start_date = datetime.datetime.now()
        super(PatientTrace, self).save(*args, ** kwargs)

