from django.db import models
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
