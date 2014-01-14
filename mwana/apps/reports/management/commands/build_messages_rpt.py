# vim: ai ts=4 sts=4 et sw=4
"""
Creates web users from a csv file. The fields in the csv file must be in the
order: FirstName, LastName, Email, Type, District. Passwords created are 'temporal'
"""

from mwana.apps.reports.models import MessageByLocationByUserType
from datetime import date
from django.db import connection

from django.core.management.base import LabelCommand
from mwana.const import DISTRICT_SLUGS
from mwana.const import PROVINCE_SLUGS
from mwana.const import ZONE_SLUGS
from rapidsms.contrib.messagelog.models import Message
from django.db import transaction

class Command(LabelCommand):
    help = "Rebuilds MessagesByMonth data for given month and year "
    args = "<year> <month>"
    label = 'Year and month, like 2020 3'

    def handle(self, * args, ** options):
        if args and args[0] == 'update':
            update()
        else:
            rebuild_messages_data()
            update()

def __del__(self):
    pass


def get_prov_dist_fac(location):
    facility = None
    district = None
    province = None

    if location:
        if location.type.slug in ZONE_SLUGS:
            facility = location.parent
            district = facility.parent
            province = district.parent
        elif location.type.slug in DISTRICT_SLUGS:
            district = location
            province = district.parent
        elif location.type.slug in PROVINCE_SLUGS:
            province = location
        else:
            facility = location
            district = facility.parent
            province = district.parent
    return province, district, facility


        
sql = '''
INSERT  into reports_messagebylocationbyusertype (count, year, month, worker_type, absolute_location_id)

SELECT count(messagelog_message.id),
extract (year from messagelog_message.date)::INTEGER  as "year"
,extract (month from messagelog_message.date)::INTEGER  as "month"
,contactsplus_contacttype.slug as worker_type
,location.id as absolute_location


from messagelog_message
join rapidsms_contact on rapidsms_contact.id = messagelog_message.contact_id
left join rapidsms_contact_types on rapidsms_contact_types.contact_id = rapidsms_contact.id
left join contactsplus_contacttype on contactsplus_contacttype.id =  rapidsms_contact_types.contacttype_id
left join locations_location location on location.id = rapidsms_contact.location_id

WHERE  extract (year from messagelog_message.date)::INTEGER = %s and extract (month from messagelog_message.date)::INTEGER = %s

group by "year", "month", worker_type, absolute_location;
'''
def rebuild_messages_data():
    today = date.today()
    years = range(2010, today.year + 1)
    months = range(1, 13)
    first_msg = Message.objects.all().order_by("date")[0]
    start_year = first_msg.date.year
    start_month = first_msg.date.month

    MessageByLocationByUserType.objects.filter(year=today.year, month=today.month).delete()
    msgs = MessageByLocationByUserType.objects.exclude(max_date=None).order_by('-max_date')
    if msgs:
        start_year = msgs[0].year
        start_month = msgs[0].month
        
    cursor = connection.cursor()

    for year in years:
        for month in months:
            if year <= start_year and month <= start_month:
                continue
            cursor.execute(sql % (year, month))
            
    transaction.commit_unless_managed()

def update():
    for mlt in MessageByLocationByUserType.objects.filter(province=None):
        # @type mlt MessageByLocationByUserType
        if mlt.absolute_location.type.slug == 'zone':
            mlt.facility_slug = mlt.absolute_location.parent.slug
            mlt.district_slug = mlt.absolute_location.parent.parent.slug
            mlt.province_slug = mlt.absolute_location.parent.parent.parent.slug
            mlt.facility = mlt.absolute_location.parent.name
            mlt.district = mlt.absolute_location.parent.parent.name
            mlt.province = mlt.absolute_location.parent.parent.parent.name
            mlt.save()
        elif mlt.absolute_location.type.slug == 'districts':
            mlt.district_slug = mlt.absolute_location.slug
            mlt.province_slug = mlt.absolute_location.parent.slug
            mlt.district = mlt.absolute_location.name
            mlt.province = mlt.absolute_location.parent.name
            mlt.save()
        elif mlt.absolute_location.type.slug == 'provinces':
            mlt.province_slug = mlt.absolute_location.slug
            mlt.province = mlt.absolute_location.name
            mlt.save()
        else:
            print mlt.absolute_location.slug
            mlt.facility_slug = mlt.absolute_location.slug
            mlt.district_slug = mlt.absolute_location.parent.slug
            mlt.province_slug = mlt.absolute_location.parent.parent.slug
            mlt.facility = mlt.absolute_location.name
            mlt.district = mlt.absolute_location.parent.name
            mlt.province = mlt.absolute_location.parent.parent.name
            mlt.save()
