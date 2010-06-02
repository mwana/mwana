import logging

from django.db import transaction
from django.conf import settings

from mwana import const
from mwana.apps.labresults.models import Payload
from mwana.apps.labresults.views import process_payload

from rapidsms.contrib.locations.models import Location

logger = logging.getLogger(__name__)

def send_results_notification(router):
    logger.debug('in send_results_notification')
    clinics_with_results =\
      Location.objects.filter(lab_results__notification_status__in=
                              ['new', 'notified']).distinct()
    labresults_app = router.get_app(const.LAB_RESULTS_APP)
    for clinic in clinics_with_results:
        logger.info('notifying %s of new results' % clinic)
        labresults_app.notify_clinic_pending_results(clinic)
        
def send_changed_records_notification(router):
    logger.debug('in send_changed_records_notification')
    clinics_with_results =\
      Location.objects.filter(lab_results__notification_status__in=
                              ['updated', 'notified']).distinct()
    labresults_app = router.get_app(const.LAB_RESULTS_APP)
    for clinic in clinics_with_results:
        logger.info('notifying %s of changed results' % clinic)
        logger.debug('notifying %s of changed results' % clinic)
        labresults_app.notify_clinic_of_changed_records(clinic)

#    if settings.SEND_LIVE_LABRESULTS:
#        clinics_with_results =\
#          Location.objects.filter(lab_results__notification_status__in=
#                                  ['new', 'notified']).distinct()
#        labresults_app = router.get_app(const.LAB_RESULTS_APP)
#        for clinic in clinics_with_results:
#            logger.info('notifying %s of new results' % clinic)
#            labresults_app.notify_clinic_pending_results(clinic)
#    else:
#        logger.info('not notifying any clinics of new results because '
#                    'settings.SEND_LIVE_LABRESULTS is False')


@transaction.commit_manually
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
