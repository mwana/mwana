# vim: ai ts=4 sts=4 et sw=4
from django.db import models
from django.db.models import Q
from mwana.apps.locations.models import Location
from rapidsms.models import Contact
import datetime



class SupplyType(models.Model):
    """
    A type of supplies, identified by a unique code and a readable name.
    Supplies might be 'batteries', 'gloves', or 'malarone'
    """
    
    slug = models.CharField(max_length=6, unique=True)
    name = models.CharField(max_length=100)
    
    def __unicode__(self):
        return self.name

STATUS_CHOICES = (
    ("requested", "yet to be processed"),
    ("processed", "processed at supplier"),
    ("sent", "processed and sent for delivery"),
    ("delivered", "processed, sent, and delivered"))

class SupplyRequest(models.Model):
    """
    A request for supplies.
    """
    
    type = models.ForeignKey(SupplyType)
    location = models.ForeignKey(Location, related_name="supply_requests")
    requested_by = models.ForeignKey(Contact, null=True, blank=True)
    status = models.CharField(max_length=9, choices=STATUS_CHOICES)
    created = models.DateTimeField(default=datetime.datetime.utcnow)
    modified = models.DateTimeField(default=datetime.datetime.utcnow)
    
    @classmethod
    def active(cls):
        """
        Return a queryset of active (non-delivered) supply requests 
        """
        return cls.objects.exclude(status="delivered")
        
        
    def __unicode__(self):
        return "Request for %s by %s at %s on %s" % \
            (self.type, self.requested_by, self.location, self.created.date()) 
    