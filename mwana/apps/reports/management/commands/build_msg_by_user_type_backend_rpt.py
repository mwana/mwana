# vim: ai ts=4 sts=4 et sw=4
"""
Builds data for reporting table
"""

from django.core.management.base import LabelCommand
from mwana.apps.reports.models import MessageByLocationUserTypeBackend
from mwana.apps.reports.models import MsgByLocationUserTypeBackendLog
from mwana.util import get_clinic_or_default
from rapidsms.contrib.messagelog.models import Message
import logging


logger = logging.getLogger(__name__)


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
        logged = MsgByLocationUserTypeBackendLog.objects.all()[0]
        if logged.locked:
            logger.info('Returning as another process has obtained lock on table')
            return
        logged.locked = True
        logger.info('Obtaining lock on table')
        logged.save()
    except IndexError:
        logged = MsgByLocationUserTypeBackendLog()
        logged.locked = True
        logged.message_id = 0
        logged.save()

    for msg in Message.objects.filter(id__gt=logged.message_id).\
                                exclude(connection=None).order_by('id')[:20000]:
        msg_year = msg.date.year
        msg_month = msg.date.month
        backend = msg.connection.backend.name
        location = get_clinic_or_default(msg.contact)
        worker_type = '|'.join(w_type.slug for w_type in msg.contact.types.all()) if msg.contact else None

        # @type mlb MessageByLocationByUserType
        try:
            mlb = MessageByLocationUserTypeBackend.objects.get(year=msg_year,
                                                         month=msg_month,
                                                         backend=backend,
                                                         absolute_location=location,
                                                         worker_type=worker_type)
            mlb.count += 1
        except MessageByLocationUserTypeBackend.DoesNotExist:
            mlb = MessageByLocationUserTypeBackend.objects.create(year=msg_year,
                                                            month=msg_month,
                                                            backend=backend,
                                                            absolute_location=location,
                                                            worker_type=worker_type,
                                                            count=1)

        if msg.direction == "I":
            mlb.count_incoming = (mlb.count_incoming or 0) + 1
        elif msg.direction == "O":
            mlb.count_outgoing = (mlb.count_outgoing or 0) + 1
            if 'DBS test results ready for you' in msg.text:
                mlb.count_DBS_notification = 1 + (mlb.count_DBS_notification or 0)
            elif 'dbs test results ready for you' in msg.text:
                mlb.count_dbs2_notification = 1 + (mlb.count_dbs2_notification or 0)
            elif 'viral load test results ready for you' in msg.text:
                mlb.count_vl_notification = 1 + (mlb.count_vl_notification or 0)

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

    logged.locked = False # release lock
    logged.save()
    logger.info('lock released')
