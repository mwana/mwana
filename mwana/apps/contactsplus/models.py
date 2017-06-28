# vim: ai ts=4 sts=4 et sw=4
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.query import QuerySet
from django.db.models.query_utils import Q
from rapidsms.models import Contact


class ContactType(models.Model):
    name = models.CharField(max_length=255)
    slug = models.CharField(unique=True, max_length=255)

    def __unicode__(self):
        return self.name


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
Contact.add_to_class("objects", SelfOrParentLocationContactManager())


class ActiveContactManager(SelfOrParentLocationContactManager):
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


class PreferredContact(models.Model):
    minor_contact = models.ForeignKey(Contact, related_name='minor_contact', unique=True, limit_choices_to={'types__slug__in': ['worker', 'cba'], 'is_active': True})
    preferred_contact = models.ForeignKey(Contact, related_name='preferred_contact', unique=True, limit_choices_to={'types__slug__in': ['worker', 'cba'], 'is_active': True})

    def clean(self):
        if not self.minor_contact.default_connection:
            raise ValidationError("Minor contact has no connection")
        if not self.preferred_contact.default_connection:
            raise ValidationError("Major contact has no connection")
        if self.minor_contact.default_connection.identity != self.preferred_contact.default_connection.identity:
            raise ValidationError("Phone numbers do not match")
        if self.minor_contact.default_connection.backend == self.preferred_contact.default_connection.backend:
            raise ValidationError("Backend is the same for both minor and preferred contacts")
        minor_backend_name = self.minor_contact.default_connection.backend.name
        major_backend_name = self.preferred_contact.default_connection.backend.name
        # TODO: use database values or settings
        if not(minor_backend_name in major_backend_name or major_backend_name in minor_backend_name):
            raise ValidationError("Backends %s and %s are not compatible" % (minor_backend_name, major_backend_name))

    def save(self, * args, ** kwargs):
        # self.clean()
        super(PreferredContact, self).save(*args, ** kwargs)

    def __unicode__(self):
        return "%s preferred over %s" % (self.preferred_contact, self.minor_contact)

    @classmethod
    def get_preferred_contact(cls, contact):
        try:
            preferred_contact = PreferredContact.objects.exclude(preferred_contact__connection=None).get(minor_contact=contact, preferred_contact__is_active=True)
            return preferred_contact.preferred_contact
        except PreferredContact.DoesNotExist:
            return contact

    @classmethod
    def get_minor_connection(cls, connection):
        try:
            preferred_contact = PreferredContact.objects.exclude(minor_contact__connection=None).\
                get(preferred_contact__connection=connection, minor_contact__is_active=True)
            return preferred_contact.minor_contact.default_connection
        except PreferredContact.DoesNotExist:
            return connection

