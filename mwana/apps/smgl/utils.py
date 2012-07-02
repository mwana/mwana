#Values that are used to indicate 'no answer' in fields of a form (especially in the case of optional values)
import datetime
from django.core.exceptions import ObjectDoesNotExist
from mwana.apps.locations.models import Location
from mwana.apps.contactsplus.models import ContactType
from rapidsms.messages.outgoing import OutgoingMessage
from mwana.apps.smgl import const 
import string
NONE_VALUES = ['none', 'n', None]

class DateFormatError(ValueError):  pass
    
def get_date(form, day_field, month_field, year_field):
    parts = [form.xpath('form/%s' % field) for field in (day_field, month_field, year_field)]
    for p in parts:
        if p in NONE_VALUES:
            return None
    try:
        intparts = [int(p) for p in parts]
    except ValueError:
        raise DateFormatError(const.DATE_NOT_NUMBERS)

    dd, mm, yy = intparts
    try:
        return datetime.date(yy,mm,dd)
    except ValueError as e:
        raise DateFormatError(str(e))

def make_date(form, dd, mm, yy, is_optional=False):
    """
    Returns a tuple: (datetime.date, ERROR_MSG)
    ERROR_MSG will be empty if datetime.date is sucesfully constructed.
    Be sure to include the dictionary key-value "date_name": DATE_NAME
    when sending out the error message as an outgoing message.
    """
    # this method has been hacked together to preserve
    # original functionality. 
    try:
        date = get_date(form, dd, mm, yy)
    except ValueError:
        return None, const.DATE_INCORRECTLY_FORMATTED_GENERAL
    
    if not date and not is_optional:
        return None, const.DATE_NOT_OPTIONAL
    
    if datetime.date(1900, 1, 1) > date:
        return None, const.DATE_YEAR_INCORRECTLY_FORMATTED

    return date, None

def get_location(slug):
    try:
        return Location.objects.get(slug__iexact=slug)
    except ObjectDoesNotExist:
        return None
    
    
def get_contacttype(slug):
    try:
        return ContactType.objects.get(slug__iexact=slug)
    except ObjectDoesNotExist:
        return None
    

def get_value_from_form(property_name, xform):
    return xform.xpath('form/%s' % property_name)

def strip_punctuation(s):
    # HT: http://stackoverflow.com/questions/265960/best-way-to-strip-punctuation-from-a-string-in-python
    return str(s).translate(string.maketrans("",""), string.punctuation)

def to_time(timestring):
    """
    Converts a time string to a time. Assumes that the timestring is a 4-digit
    numeric string between 0000 and 2359 (although it will do a bit of work
    to clean up the string)
    """
    timestring = strip_punctuation(timestring).strip()
    if (len(timestring) != 4):
        raise ValueError(const.TIME_INCORRECTLY_FORMATTED % {"time": timestring})
    hh = timestring[:2]
    mm = timestring[2:]
    try:
        hh = int(hh)
        mm = int(mm)
    except ValueError:
        raise ValueError(const.TIME_INCORRECTLY_FORMATTED % {"time": timestring})
    return datetime.time(hh, mm)

def send_msg(connection, txt, router, **kwargs):
    router.outgoing(OutgoingMessage(connection, txt, **kwargs))
