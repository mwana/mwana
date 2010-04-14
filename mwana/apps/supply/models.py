from django.db import models
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
    place = models.ForeignKey(Location, null=True, blank=True)
    requestor = models.ForeignKey(Contact, null=True, blank=True)
    status = models.CharField(max_length=9, choices=STATUS_CHOICES)
    created = models.DateTimeField(default=datetime.datetime.utcnow)
    modified = models.DateTimeField(default=datetime.datetime.utcnow)
    
    def __unicode__(self):
        return "Request for %s at %s on %s" % (self.type, self.place, self.created.date()) 
    