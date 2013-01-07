#Values that are used to indicate 'no answer' in fields of a form (especially in the case of optional values)
import csv
import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.db.models.query import QuerySet
from django.http import HttpResponse

from mwana.apps.locations.models import Location
from mwana.apps.contactsplus.models import ContactType
from rapidsms.messages.outgoing import OutgoingMessage
from rapidsms.contrib.messagelog.models import Message, DIRECTION_CHOICES
from mwana.apps.smgl import const
import string
NONE_VALUES = ['none', 'n', None, '']


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
        return datetime.date(yy, mm, dd)
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

    if date and datetime.date(1900, 1, 1) > date:
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


def mom_or_none(val):
    """
    Returns None if the string is explicitly empty, otherwise looks up
    a mother based on the ID, and raises a DoesNotExist exception if
    that's not found.
    """
    from mwana.apps.smgl.models import PregnantMother
    if val.lower() == "none":
        return None
    else:
        return PregnantMother.objects.get(uid=val)


def get_value_from_form(property_name, xform):
    return xform.xpath('form/%s' % property_name)


def strip_punctuation(s):
    # HT: http://stackoverflow.com/questions/265960/best-way-to-strip-punctuation-from-a-string-in-python
    return str(s).translate(string.maketrans("", ""), string.punctuation)


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


def get_session_message(session, direction='I'):
    """
    Saves the Inbound or Outbound message to an XFormsSession object
    """
    if direction in [x[0] for x in DIRECTION_CHOICES]:
        msg_set = Message.objects.filter(connection=session.connection,
                                         direction=direction
                              ).order_by('id')
        if direction == 'I':
            msg_set = msg_set.filter(
                            text__icontains=session.trigger.trigger_keyword
                            )
            session.message_incoming = msg_set.reverse()[0]
        else:
            session.message_outgoing = msg_set.reverse()[0]
        session.save()


def filter_by_dates(qs, field, start=None, end=None):
    """
    Utility to filter querysets by optional start/end dates
    """
    filters = {}
    if start:
        key = '{0}__gte'.format(field)
        filters[key] = start
    if end:
        key = '{0}__lte'.format(field)
        filters[key] = end
    return qs.filter(**filters)


def export_as_csv(records, keys, filename):
    """
    export a set of records as CSV
    """
    response = HttpResponse(mimetype='text/csv')
    disposition = 'attachment; filename="{0}"'.format(filename)
    response['Content-Disposition'] = disposition
    if type(records) == QuerySet:
        writer = csv.writer(response)
        for r in records:
            writer.writerow([getattr(r, key) for key in keys])
    else:
        dict_writer = csv.DictWriter(response, keys)
        dict_writer.writer.writerow(keys)
        dict_writer.writerows(records)
    return response


def get_current_district(location):
    """
    Returns the district associated with the current location
    """
    loc_type = location.type.singular.lower()
    while loc_type != 'district':
        location = location.parent
        try:
            loc_type = location.type.singular.lower()
        except AttributeError:
            return None
    return location


def get_location_tree_nodes(location, locations=None):
    """
    Returns the children of a given province
    """
    if not locations:
        locations = []
    for child in location.location_set.all():
        locations.append(child)
        get_location_tree_nodes(child, locations)
    locations = sorted(locations, key=lambda loc: loc.name)
    return locations


def percentage(part, whole, extended=None):
    if whole != 0:
        result = 100 * float(part) / float(whole)
        if extended:
            return "{0:.5f}%".format(result)
        return "{0:.2f}%".format(result)
    return 0


def mother_death_ratio(part, whole):
    if whole != 0:
        result = part / float(whole) * 100000
        return "{0:.0f}".format(result)
    return 0


def get_default_dates(days=14):
    """
    Return a start and end date values for the supplied range of days
    """
    end_date = datetime.datetime.today().date()
    start_date = end_date - datetime.timedelta(days=days)
    return start_date, end_date

