# vim: ai ts=4 sts=4 et sw=4
"""
Updates Reporting table MessageByLocationByUserType
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
    help = "Rebuilds MessageByLocationByUserType data for given month and year "
    args = "<year> <month>"
    label = 'Year and month, like 2020 3'

    def handle(self, * args, ** options):
        if args and args[0] == 'update':
            update_locations()
        else:
            rebuild_messages_data()
            update_locations()


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
INSERT  into reports_messagebylocationbyusertype ( year,
month,
absolute_location_id,
worker_type,
count,
count_incoming,
count_outgoing)


select
year,
month,
absolute_location,
worker_type,
count,
count_incoming ,
count_outgoing

from
(select
counts.year,
counts.month,
counts.absolute_location,
counts.worker_type,
sum(counts.count) count,
sum(count_incoming) count_incoming,
sum(count_outgoing) count_outgoing

from (

SELECT count(messagelog_message.id),
extract (year from messagelog_message.date)::INTEGER  as "year"
,extract (month from messagelog_message.date)::INTEGER  as "month"
,contactsplus_contacttype.slug as worker_type
,case locations_locationtype.slug when 'zone' then location.parent_id else location.id end as absolute_location

from messagelog_message
join rapidsms_contact on rapidsms_contact.id = messagelog_message.contact_id
left join rapidsms_contact_types on rapidsms_contact_types.contact_id = rapidsms_contact.id
left join contactsplus_contacttype on contactsplus_contacttype.id =  rapidsms_contact_types.contacttype_id
join locations_location location on location.id = rapidsms_contact.location_id
  left join locations_locationtype on locations_locationtype.id= location.type_id

WHERE  extract (year from messagelog_message.date)::INTEGER = {year} and extract (month from messagelog_message.date)::INTEGER = {month}

group by "year", "month", worker_type, absolute_location) counts


----
left join (

SELECT count(messagelog_message.id) as count_incoming,
extract (year from messagelog_message.date)::INTEGER  as "year"
,extract (month from messagelog_message.date)::INTEGER  as "month"
,contactsplus_contacttype.slug as worker_type
,case locations_locationtype.slug when 'zone' then location.parent_id else location.id end as absolute_location

from messagelog_message
join rapidsms_contact on rapidsms_contact.id = messagelog_message.contact_id
left join rapidsms_contact_types on rapidsms_contact_types.contact_id = rapidsms_contact.id
left join contactsplus_contacttype on contactsplus_contacttype.id =  rapidsms_contact_types.contacttype_id
join locations_location location on location.id = rapidsms_contact.location_id  left join locations_locationtype on locations_locationtype.id= location.type_id

WHERE  direction = 'I'
and extract (year from messagelog_message.date)::INTEGER = {year} and extract (month from messagelog_message.date)::INTEGER = {month}

group by "year", "month", worker_type, absolute_location) count_incoming
on counts.absolute_location = count_incoming.absolute_location and counts.year=count_incoming.year and counts.month=count_incoming.month
and counts.worker_type= count_incoming.worker_type
--
left join (

SELECT count(messagelog_message.id) as count_outgoing,
extract (year from messagelog_message.date)::INTEGER  as "year"
,extract (month from messagelog_message.date)::INTEGER  as "month"
,contactsplus_contacttype.slug as worker_type
,case locations_locationtype.slug when 'zone' then location.parent_id else location.id end as absolute_location

from messagelog_message
join rapidsms_contact on rapidsms_contact.id = messagelog_message.contact_id
left join rapidsms_contact_types on rapidsms_contact_types.contact_id = rapidsms_contact.id
left join contactsplus_contacttype on contactsplus_contacttype.id =  rapidsms_contact_types.contacttype_id
join locations_location location on location.id = rapidsms_contact.location_id  left join locations_locationtype on locations_locationtype.id= location.type_id

WHERE  direction = 'O'
and extract (year from messagelog_message.date)::INTEGER = {year} and extract (month from messagelog_message.date)::INTEGER = {month}

group by "year", "month", worker_type, absolute_location) count_outgoing
on counts.absolute_location = count_outgoing.absolute_location and counts.year=count_outgoing.year and counts.month=count_outgoing.month
and counts.worker_type= count_outgoing.worker_type


group by counts.year,
counts.month,
counts.absolute_location,
counts.worker_type) table1;
'''


def rebuild_messages_data():
    today = date.today()
    years = range(2010, today.year + 1)
    months = range(1, 13)
    first_msg = Message.objects.all().order_by("date")[0]
    start_year = first_msg.date.year
    start_month = first_msg.date.month
    last_imported_year = start_year
    last_imported_month = start_month - 1

    MessageByLocationByUserType.objects.filter(year=today.year, month=today.month).delete()
    MessageByLocationByUserType.objects.filter(absolute_location__name='Training Clinic').delete()
    msgs = MessageByLocationByUserType.objects.all().order_by('-year')
    if msgs:
        last_imported_year = msgs[0].year
        last_imported_month = msgs.filter(year=last_imported_year).order_by('-month')[0].month
        
    cursor = connection.cursor()

    for year in years:
        for month in months:
            if year < last_imported_year:
                continue
            if year == start_year and month < start_month:
                continue
            if year == last_imported_year and month <= last_imported_month:
                continue
            cursor.execute(sql.format(year=year, month=month))
            
    transaction.commit_unless_managed()


def update_locations():
    for mlt in MessageByLocationByUserType.objects.filter(province=None):

#        print mlt.absolute_location.slug, mlt.id
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
            mlt.facility_slug = mlt.absolute_location.slug
            mlt.district_slug = mlt.absolute_location.parent.slug
            mlt.province_slug = mlt.absolute_location.parent.parent.slug
            mlt.facility = mlt.absolute_location.name
            mlt.district = mlt.absolute_location.parent.name
            mlt.province = mlt.absolute_location.parent.parent.name
            mlt.save()
