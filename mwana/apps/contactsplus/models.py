from django.db import models
from django.db.models.query import QuerySet
from django.db.models.query_utils import Q
from rapidsms.models import Contact

class ContactType(models.Model):
    name = models.CharField(max_length=255)
    slug = models.CharField(unique=True, max_length=255)

    def __unicode__(self):
        return self.name

class ActiveContactManager(models.Manager):
    """Filter contacts by who is active"""
    
    def get_query_set(self):
        return super(ActiveContactManager, self).get_query_set()\
                    .filter(is_active=True)

# add the active manager to the Contact class.  You can reference this
# instead of objects like:
#     Contact.active.all()   
#     Contact.active.filter(name="mary")
# etc.
Contact.add_to_class("active", ActiveContactManager())

class SelfOrParentLocationQuerySet(QuerySet):
    """
    Query set to filter by a location looking in both the location 
    and location parent field.  Call it like:
    
        objects.filter(name="mary").location(my_loc)

    """
    
    def location(self, location):
        return self.filter(Q(location=location)|Q(location__parent=location))

class SelfOrParentLocationContactManager(models.Manager):
    """
    Manager to filter by a location looking in both the location 
    and location parent field. Call it like:
    
        objects.location(my_loc).filter(name="mary")

    """
    
    def location(self, location):
        return self.get_query_set().location(location)
        
    def get_query_set(self):
        return SelfOrParentLocationQuerySet(self.model)

# override the Contacts manager so you can do location aware queries
Contact.add_to_class("objects",SelfOrParentLocationContactManager())

