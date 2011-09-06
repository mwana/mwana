# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.locations.models import Location, LocationType
from mwana import const
import datetime
from django.conf import settings
from mwana.importlib import get_class


LocationCode = get_class(settings.LOCATION_CODE_CLASS)


def get_clinic_or_default(contact):
    """Gets a clinic associated with the contact"""
    
    if contact is None:   return None
    
    # implementation-wise this is a mess because of the list 
    # of possible clinic types.  For now we just return the
    # first parent that is not a zone type or the location
    # associated with the contact directly, if no non-zone
    # parents are found 
    location = contact.location
    while location:
        if location.type.slug not in const.ZONE_SLUGS:
            return location
        location = location.parent
    return contact.location


def is_today_a_weekend():
    """
    Returns true if current date is a weekend. Monday => 0
    """
    return datetime.date.today().weekday() in [5, 6]


def is_weekend(input_date):
    """
    Returns true if passed date is a weekend. Monday => 0
    """
    return input_date.weekday() in [5, 6]

def get_contact_type_name(contact):
    '''
    Returns the worker_type (name) based on the contact
    '''
    try:
        return contact.types.all()[0].name
    except (AttributeError, IndexError):
        return ""

def get_contact_type_slug(contact):
    '''
    Returns the worker_type (slug) based on the contact
    '''
    try:
        return contact.types.all()[0].slug
    except (AttributeError, IndexError):
        return ""

def get_worker_type(category):
    '''
    Returns the worker_type based on the category
    '''
    type = category.lower()
    if type == 'district' or type == 'dho':
        return const.get_district_worker_type()
    elif type == 'clinic':
        return const.get_clinic_worker_type()
    if type == 'cba':
        return const.get_cba_type()
    elif type == 'province' or type == 'pho':
        return const.get_province_worker_type()
    elif type == 'hub':
        return const.get_hub_worker_type()
    elif type == 'lab':
        return const.get_lab_worker_type()

def get_location_type(category):
    '''
    Returns the location_type based on the category
    '''
    type = category.lower()
    if type == 'district' or type == 'dho':
        return const.DISTRICT_SLUGS
    elif type == 'clinic':
        return const.CLINIC_SLUGS
    if type == 'cba':
        return const.ZONE_SLUGS
    elif type == 'province' or type == 'pho':
        return const.PROVINCE_SLUGS
    elif type == 'hub':
        return const.CLINIC_SLUGS
    elif type == 'lab':
        return const.CLINIC_SLUGS
