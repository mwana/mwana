from django.db import models
from django.db.models import Q
from rapidsms.contrib.locations.models import Location
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
    ("requested", "Requested"), 
    ("processed", "Processed"), 
    ("sent", "Sent"), 
    ("delivered", "Delivered"))


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
        return "Request for %s at %s on %s" % (self.type, self.location, self.created.date()) 
    