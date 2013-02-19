# vim: ai ts=4 sts=4 et sw=4
from django.db import models




class BlacklistedPeople(models.Model):
    """
    Lists ONLY PEOPLE who have been blacklisted. Don't include other numbers
    """

    phone = models.CharField(max_length=15)
    date_created = models.DateTimeField(auto_now_add=True, editable=False)
    edited_on = models.DateTimeField(auto_now=True)
    valid = models.NullBooleanField(null=True, blank=True, editable=False, default=True)

    def __unicode__(self):
        return self.phone

