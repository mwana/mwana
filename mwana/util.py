from mwana.apps.locations.models import LocationType
from mwana import const
import datetime

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
