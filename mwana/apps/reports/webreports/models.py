# vim: ai ts=4 sts=4 et sw=4
from django.contrib.auth.models import User
from django.db import models
from mwana.apps.locations.models import Location


class ReportingGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __unicode__(self):
        return self.name


class GroupUserMapping(models.Model):
    user = models.ForeignKey(User)
    group = models.ForeignKey(ReportingGroup)

    def __unicode__(self):
        return "%s: %s" % (self.user, self.group)

    class Meta:
        unique_together = (('group', 'user'),)


class GroupFacilityMapping(models.Model):
    group = models.ForeignKey(ReportingGroup)
    facility = models.ForeignKey(Location, limit_choices_to={
        "send_live_results": True})

    def __unicode__(self):
        return "%s: %s" % (self.group, self.facility)

    class Meta:
        unique_together = (('group', 'facility'),)


class UserPreference(models.Model):
    user = models.ForeignKey(User)
    preference_name = models.CharField(max_length=100)
    preference_value = models.SmallIntegerField(default=-1)
    extra_preference_value = models.CharField(max_length=100, null=True, blank=True)

    def __unicode__(self):
        return "%s %s: %s" % (self.user, self.preference_name, self.preference_value)

    class Meta:
        unique_together = (('user', 'preference_name'))
