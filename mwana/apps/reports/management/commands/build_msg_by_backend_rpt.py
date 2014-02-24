# vim: ai ts=4 sts=4 et sw=4
"""
Builds data for reporting table
"""

from django.core.management.base import LabelCommand
from mwana.apps.reports.models import MessageByLocationByBackend
from mwana.apps.reports.models import MsgByLocationByBackendBuildLog
from mwana.util import get_clinic_or_default
from rapidsms.contrib.messagelog.models import Message

class Command(LabelCommand):
    help = ""
    args = ""
    label = ''

    def handle(self, * args, ** options):
        rebuild_messages_data()

def __del__(self):
    pass
     

def rebuild_messages_data():
   
    try:
        logged  = MsgByLocationByBackendBuildLog.objects.all()[0]
    except IndexError:
        logged = MsgByLocationByBackendBuildLog()
        logged.lock = 1
        logged.message_id = 0
        logged.save()


    for msg in Message.objects.filter(id__gt=logged.message_id).\
                                exclude(connection=None).order_by('id'):
        # @type msg Message
        msg_year = msg.date.year
        msg_month = msg.date.month
        backend = msg.connection.backend.name
        location = get_clinic_or_default(msg.contact)

        # @type mlb MessageByLocationByBackend
        try:
            mlb = MessageByLocationByBackend.objects.get(year=msg_year,
                                                         month=msg_month,
                                                         backend=backend,
                                                         absolute_location=location)
            mlb.count = mlb.count + 1
        except MessageByLocationByBackend.DoesNotExist:
            mlb = MessageByLocationByBackend.objects.create(year=msg_year,
                                                            month=msg_month,
                                                            backend=backend,
                                                            absolute_location=location,
                                                            count=1)

        if msg.direction == "I":
            mlb.count_incoming = mlb.count_incoming + 1 if mlb.count_incoming != None else 0
        elif msg.direction == "O":
            mlb.count_outgoing = mlb.count_outgoing + 1 if mlb.count_outgoing != None else 0

        if mlb.absolute_location:
            if mlb.absolute_location.type.slug == 'zone':
                mlb.facility_slug = mlb.absolute_location.parent.slug
                mlb.district_slug = mlb.absolute_location.parent.parent.slug
                mlb.province_slug = mlb.absolute_location.parent.parent.parent.slug
                mlb.facility = mlb.absolute_location.parent.name
                mlb.district = mlb.absolute_location.parent.parent.name
                mlb.province = mlb.absolute_location.parent.parent.parent.name
                mlb.save()
            elif mlb.absolute_location.type.slug == 'districts':
                mlb.district_slug = mlb.absolute_location.slug
                mlb.province_slug = mlb.absolute_location.parent.slug
                mlb.district = mlb.absolute_location.name
                mlb.province = mlb.absolute_location.parent.name
            elif mlb.absolute_location.type.slug == 'provinces':
                mlb.province_slug = mlb.absolute_location.slug
                mlb.province = mlb.absolute_location.name
            else:
                mlb.facility_slug = mlb.absolute_location.slug
                mlb.district_slug = mlb.absolute_location.parent.slug
                mlb.province_slug = mlb.absolute_location.parent.parent.slug
                mlb.facility = mlb.absolute_location.name
                mlb.district = mlb.absolute_location.parent.name
                mlb.province = mlb.absolute_location.parent.parent.name

        mlb.save()
        logged.message_id = msg.id
        logged.save()
