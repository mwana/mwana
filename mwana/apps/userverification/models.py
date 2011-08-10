# vim: ai ts=4 sts=4 et sw=4
from datetime import datetime

from django.db import models
from mwana.apps.locations.models import Location
from rapidsms.models import Contact

class UserVerification(models.Model):
    """
    Virifies if users(clinic workers) are still working at their register facilities
    """
    VERIFICATION_FREQ = (
                         ('Q', 'Querterly'),
                         ('M', 'Monthly'),
                         ('A', '2.5 Months'),
                         )

    REQUEST_TYPES = (
                     ('1', 'Still using Results160/At same clinic?'),
                     ('2', 'Other'),
                     )

    facility = models.ForeignKey(Location, limit_choices_to={'parent__type__slug': 'districts'})
    contact = models.ForeignKey(Contact, limit_choices_to={'types__slug': 'clinic_worker'})

    verification_freq    = models.CharField(choices=VERIFICATION_FREQ, max_length=1, blank=True)
    request    = models.CharField(choices=REQUEST_TYPES, max_length=1, blank=True)
    response = models.CharField(max_length=500, blank=True, null=True)
    responded = models.BooleanField()
    request_date     = models.DateTimeField(default=datetime.now)
    response_date     = models.DateTimeField(blank=True, null=True)


    def __unicode__(self):
        return "%s asked on %s. Responded on %s with %s" % (self.contact.name,
                                                            self.request_date,
                                                            self.response_date,
                                                            self.response)