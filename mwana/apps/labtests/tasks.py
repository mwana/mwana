# vim: ai ts=4 sts=4 et sw=4
import logging
from django.conf import settings

from django.db.models import Q
from django.db import transaction
from django.conf import settings

from mwana import const
from mwana.apps.labtests.models import Payload
from mwana.apps.labtests.views import process_payload

from mwana.apps.locations.models import Location


logger = logging.getLogger(__name__)

verified = Q(test_results__verified__isnull=True) |\
           Q(test_results__verified=True)

send_live_results = Q(test_results__clinic__send_live_results=True)

viral_load = Q(test_results__test_type__isnull=True) |\
           Q(test_results__test_type=const.get_viral_load_type())

dbs = Q(test_results__test_type=const.get_dbs_type())


def send_vl_results_notification(router):
    logger.debug('in send_vl_results_notification')
    if settings.SEND_LIVE_LABRESULTS:
        facility_type = Q(type__slug__in=const.CLINIC_SLUGS)
        new_notified = Q(test_results__notification_status__in=
                         ['new', 'notified'])
        clinics_with_results =\
          Location.objects.filter(new_notified & verified & send_live_results & viral_load, facility_type).distinct()
        testresults_app = router.get_app("mwana.apps.labtests")

        for clinic in clinics_with_results:
            logger.info('notifying %s of new results' % clinic)
            testresults_app.notify_clinic_pending_results(clinic, const.get_viral_load_type())
    else:
        logger.info('not notifying any clinics of new results because '
                    'settings.SEND_LIVE_LABRESULTS is False')

def send_dbs_results_notification(router):
    logger.debug('in send_vl_results_notification')
    if settings.SEND_LIVE_LABRESULTS:
        facility_type = Q(type__slug__in=const.CLINIC_SLUGS)
        new_notified = Q(test_results__notification_status__in=
                         ['new', 'notified'])
        clinics_with_results =\
          Location.objects.filter(new_notified & verified & send_live_results & dbs, facility_type).distinct()
        testresults_app = router.get_app("mwana.apps.labtests")

        for clinic in clinics_with_results:
            logger.info('notifying %s of new results' % clinic)
            testresults_app.notify_clinic_pending_results(clinic, const.get_dbs_type())
    else:
        logger.info('not notifying any clinics of new results because '
                    'settings.SEND_LIVE_LABRESULTS is False')

def send_results_ready_notification_to_participant(router):
    logger.debug('in send_results_notification')
    if settings.SEND_LIVE_LABRESULTS:
        testresults_app = router.get_app("mwana.apps.labtests")

        testresults_app.send_pending_participant_notifications()
    else:
        logger.info('not participants of new results because '
                    'settings.SEND_LIVE_LABRESULTS is False')


#@transaction.commit_manually
def process_outstanding_payloads(router):
    logger.debug('in process_outstanding_payloads')
    for payload in Payload.objects.filter(parsed_json=True,
                                          validated_schema=False):
        try:
            process_payload(payload)
            transaction.commit()
        except:
            logger.exception('failed to parse payload %s' % payload)
            transaction.rollback()
