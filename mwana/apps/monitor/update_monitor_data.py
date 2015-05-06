import logging
from mwana.apps.labresults.models import Payload, Result
from mwana.apps.labresults.views import process_payload
from mwana.apps.monitor.tasks import import_monitor_samples

logger = logging.getLogger(__name__)


def process_outstanding_payloads():
    logger.debug('in process_outstanding_payloads')
    for payload in Payload.objects.filter(parsed_json=True,
                                          incoming_date__year=2015):
        try:
            process_payload(payload)
            logger.debug('successfully processed payload: %s : %s ' % (
                payload.id, payload))
        except:
            logger.exception('failed to parse payload %s : %s' % (
                payload.id, payload))

labs = ['lilongwe/kch', 'blantyre/queens', 'blantyre/dream', 'mzuzu/central',
        'mzimba/mdh', 'zomba/zch', 'lilongwe/pih']

# process_outstanding_payloads()
# import_monitor_samples(labs, True)
