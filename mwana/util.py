from rapidsms.contrib.locations.models import LocationType
from mwana.const import get_zone_type

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
        if location.type != get_zone_type():
            return location
        location = location.parent
    return contact.location