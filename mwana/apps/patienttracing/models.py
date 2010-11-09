import datetime

from django.db import models
from rapidsms.models import Contact
from mwana.apps.reminders.models import PatientEvent

STATUS_CHOICES = (
                  ("new", "new"),
                  ("told", "told"),
                  ("confirmed", "confirmed"),
                  ("refused", "patient refused"),# when mother can't be traced
                  ("lost", "lost to followup"),# when mother can't be traced
                  ("dead", "patient died"),# when mother can't be traced
                  )


class PatientTrace(models.Model):
    # person who initiates the tracing
    initiator = models.ForeignKey(Contact, related_name='patients_traced',
                                     limit_choices_to={'types__slug': 'clinic_worker'},
                                     null=True, blank=True)
    type = models.CharField(max_length=15)
    name = models.CharField(max_length=50) # name of patient to trace
    patient_event = models.ForeignKey(PatientEvent, related_name='patient_traces',
                                limit_choices_to={'types__slug': 'patient'},
                                null=True, blank=True) 
    messenger = models.ForeignKey(Contact,  related_name='patients_reminded',
                            limit_choices_to={'types__slug': 'cba'}, null=True,
                            blank=True)# cba who informs patient

    confirmed_by = models.ForeignKey(Contact, related_name='patient_traces_confirmed',
                            limit_choices_to={'types__slug': 'cba'}, null=True,
                            blank=True)# cba who confirms that patient visited clinic

    status = models.CharField(choices=STATUS_CHOICES, max_length=15) # status of tracing activity

    start_date = models.DateTimeField() # date when tracing starts
    reminded_on = models.DateTimeField(null=True, blank=True) # date when cba tells mother
    confirmed_date = models.DateTimeField(null=True, blank=True)# date of confirmation that patient visited clinic   
    

    def save(self, * args, ** kwargs):
        if not self.pk:
            self.start_date = datetime.datetime.now()
        super(PatientTrace, self).save(*args, ** kwargs)

