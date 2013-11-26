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
import xlwt

NONE_VALUES = ['none', 'n', None, '']


class DateFormatError(ValueError):  pass

def excel_export_header(worksheet, row_index=0, selected_indicators=[], selected_level=None, additional_filters=[], start_date=None, end_date=None):    
    if selected_level:
        location_level = "%s: %s" %(selected_level.type.singular.title(), selected_level.name)
    else:
        location_level = "National"
    start_date = start_date.strftime('%m/%d/%y') if start_date else ''
    end_date = end_date.strftime('%m/%d/%y') if end_date else ''
    
    bold_style = xlwt.easyxf('font: bold 1')
    date_format = xlwt.easyxf('align: horiz left;', num_format_str='mm/dd/yyyy')
    heading_style = xlwt.easyxf('font: bold 1, height 350; align: vert center; align: horiz center;')
    worksheet.write_merge(row_index, row_index, 0, 1, 'mUbumi Data Export', heading_style)
    
    worksheet.col(0).width = 30*256#The the 30 should probably be dynamically selected based on the biggest string in column 0
    worksheet.col(1).width = 22*256
    worksheet.row(row_index).height = 500 
    
    row_index += 2
    worksheet.write(row_index, 0, 'Export Date:', bold_style)
    worksheet.write(row_index, 1, datetime.datetime.now().date(), date_format)
    
    row_index += 1
    worksheet.write(row_index, 0, 'Selected Indicators:', bold_style)
    worksheet.write(row_index, 1, ",".join(selected_indicators))
    
    row_index += 1
    worksheet.write(row_index, 0, 'Selected Level:', bold_style)
    worksheet.write(row_index, 1, location_level)
    
    if additional_filters:
        row_index += 1
        worksheet.write(row_index, 0, 'Additional Filters:', bold_style)
        worksheet.write(row_index, 1, ';'.join(additional_filters))
        
    row_index += 1
    worksheet.write(row_index, 0, 'Selected Timeframe:', bold_style)
    worksheet.write(row_index, 1, " - ".join([start_date, end_date]))
    
    row_index += 1
    return worksheet, row_index

def write_excel_columns(worksheet, row_index, column_headers):
    bold_style = xlwt.easyxf('font: bold 1')
    for column_header, index in enumerate(column_headers):
        worksheet.write(row_index, column_header, index, bold_style)
    
    row_index += 1  
    return worksheet, row_index

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

def get_location_and_parents_types(location, facility_types={}):
    """Returns a dictionary mapping the location to its type including 
    all its ancestor locations mapped to their types in no particular order.
    The returned dictionary has the location type slugs which are plural for province/district/zone
    so expect {'districts': 'xxxx', 'provinces': 'yyyyy'}"""
    facility_types[location.type.slug] = location.name
    if location.parent:
        return get_location_and_parents_types(location.parent, facility_types)
    else:
        return facility_types
    
def get_district_facility_zone(location):
    facility = None
    location_parents_types = get_location_and_parents_types(location)
    facility = location_parents_types.get('rural_health_centre', None)
    if not facility:
        location_parents_types.get('urban_health_centre', None)
        
    zone = location_parents_types.get('zone', None)
    district = location_parents_types.get('districts', None)
    return district, facility, zone
        
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
    cleaned = strip_punctuation(timestring).strip()
    if len(cleaned) == 3:
        cleaned = '0%s' % cleaned
    if (len(cleaned) != 4):
        raise ValueError(const.TIME_INCORRECTLY_FORMATTED % {"time": timestring})
    hh = cleaned[:2]
    mm = cleaned[2:]
    try:
        hh = int(hh)
        mm = int(mm)
    except ValueError:
        raise ValueError(const.TIME_INCORRECTLY_FORMATTED % {"time": timestring})
    return datetime.time(hh, mm)

def send_msg(connection, txt, router, **kwargs):
    router.outgoing(OutgoingMessage(connection, txt, **kwargs))

def respond_to_session(router, session, outgoing_text, is_error=False,
                       **message_kwargs):
    router.outgoing(OutgoingMessage(session.connection, outgoing_text,
                                    **message_kwargs))
    update_session_message(session, direction='O')
    if is_error:
        session.has_error = True
        session.save()
    return True

def update_session_message(session, direction='I'):
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
        #convert to datetime object
        end = datetime.datetime.combine(end, datetime.time(hour=23, minute=59, second=59))
        key = '{0}__lte'.format(field)
        filters[key] = end
    return qs.filter(**filters)


def export_as_csv(records, keys, filename):
    """
    export a set of records as CSV
    """
    if '.' not in filename:
        filename = '%s.csv' % filename
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


def get_location_tree_nodes(location, locations=None, *qs, **extras):
    """
    Returns the children of a given province
    """
    qs = qs or []
    if not locations:
        locations = []
    for child in location.location_set.filter(*qs, **extras):
        locations.append(child)
        get_location_tree_nodes(child, locations, *qs, **extras)
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

