# vim: ai ts=4 sts=4 et sw=4
import logging
from django.conf import settings
from django.db.models import Q
from mwana import const
from mwana.apps.locations.models import Location

logger = logging.getLogger(__name__)

verified = Q(lab_results__verified__isnull=True) | \
    Q(lab_results__verified=True)

send_live_results = Q(lab_results__clinic__send_live_results=True)

def send_results_to_printer(router):
    logger.debug('in tasks.send_results_to_printer')
    if settings.SEND_LIVE_LABRESULTS:
        new_notified = Q(lab_results__notification_status__in=
                         ['new', 'notified'])

        clinics_with_results = \
            Location.objects.filter(Q(has_independent_printer=True)
                                    & new_notified
                                    & verified & send_live_results).distinct()
        labresults_app = router.get_app(const.LAB_RESULTS_APP)
        for clinic in clinics_with_results:
            logger.info('sending new results to printer at %s' % clinic)
            labresults_app.send_printers_pending_results(clinic)
    else:
        logger.info('not sending new results because '
                    'settings.SEND_LIVE_LABRESULTS is False')
