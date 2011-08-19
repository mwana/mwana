#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from pygrowup.pygrowup import helpers
from django.db import models

class Patient(models.Model):
    PATIENT_STATUS = (
		 ("NA","NA"),
		 ("NAM",""),
                 ("MAM","Moderate Malnutrition"),
                 ("SAM","Severe Malnutrition"),
                 ("W","Wasting"),
                 ("S","Stunting"),)

    status          = models.CharField(max_length=1000,choices=PATIENT_STATUS,default="",blank=True)
    household_id    = models.PositiveIntegerField(max_length=10, blank=True, null=True)
    cluster_id      = models.PositiveIntegerField(max_length=10, blank=True, null=True)
    age_in_months   = models.PositiveIntegerField(max_length=10, blank=True, null=True)

    @property
    def assessments(self):
        return Assessment.objects.filter(patient=self.patient).order_by('-patient__last_updated')

    def latest_assessment(self):
        if len(self.assessments) > 0:
            return self.assessments[0]
        else:
            return None

    @property
    def age_in_months_from_date_of_birth(self):
        if self.date_of_birth is not None:
            return helpers.date_to_age_in_months(self.date_of_birth)

    def __unicode__(self):
        return "Child %s" % (self.code)

    def status_from_bools(self, mam, sam, stunting):
        if not mam and not sam and not stunting:
            return "NAM"
        #(False,True):"SAM"
        elif sam and not mam:
            return "SAM"
        #(False,False):"NAM"
        elif mam and not sam:
            return "MAM"
        elif stunting:
            return "S"
        #(True,False):"MAM"
        elif not mam and not sam:
            return "NAM"
        else:
            return "NA"

    class Meta:
        abstract = True
        verbose_name = "Patient"
