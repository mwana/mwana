# vim: ai ts=4 sts=4 et sw=4
from django.db import models
from mwana.apps.locations.models import Location
#from rapidsms.models import Connection
from django.contrib.auth.models import User

class ReportingGroup(models.Model):
    name = models.CharField(max_length=100,unique=True)

    def __unicode__(self):
        return self.name
    

class GroupUserMapping(models.Model):
    user = models.ForeignKey(User)
    group = models.ForeignKey(ReportingGroup)

    def __unicode__(self):
        return "%s: %s"%(self.user,self.group)

class GroupFacilityMapping(models.Model):
    group = models.ForeignKey(User)
    facilty = models.ForeignKey(Location)

    def __unicode__(self):
        return "%s: %s"%(self.group,self.facilty)
