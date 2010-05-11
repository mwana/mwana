import logging

from mwana import const
from mwana.apps.labresults.models import Result
from rapidsms import router
from rapidsms.contrib.locations.models import Location

logger = logging.getLogger(__name__)

def send_results_notification (self):
    logger.debug('in send_results_notification')
    clinics_with_results =\
      Location.objects.filter(lab_results__notification_status__in=
                              ['new', 'notified']).distinct()
    labresults_app = router.router.get_app(const.LAB_RESULTS_APP)
    for clinic in clinics_with_results:
        logger.info('notifying %s of new results' % clinic)
        labresults_app.notify_clinic_pending_results(clinic)
