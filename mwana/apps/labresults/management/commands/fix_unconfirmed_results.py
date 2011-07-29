# vim: ai ts=4 sts=4 et sw=4
"""
Sets labresults.Result.result_sent_date to the the value the result was sent for
results that were sent before this field was added. The dates are extracted from
message logs
"""

from django.core.management.base import CommandError
from django.core.management.base import LabelCommand
from mwana.apps.labresults.models import Result
import logging
from datetime import datetime
from datetime import timedelta


from mwana.apps.labresults.messages import TEST_TYPE
from mwana.apps.labresults.models import Result


from mwana.apps.tlcprinters.models import MessageConfirmation

logger = logging.getLogger(__name__)



class Command(LabelCommand):
    help = """
    Marks results previously sent to printer but not confirmed as having not
    been sent. Also marks the corresponding confirmation messages as confirmed
    """
    args = "<clinic name>"
    label = 'clinic name'
    
    def handle(self, * args, ** options):
        if len(args) < 1:
            raise CommandError('Please specify %s.' % self.label)
        clean_up_unconfirmed_results(args[0])
                
    def __del__(self):
        pass

def clean_up_unconfirmed_results(param_clinic):
    """
    Marks results previously sent to printer but not confirmed as having not
    been sent. Also marks the corresponding confirmation messages as confirmed
    """

    param_clinic = param_clinic.lower()
    today = datetime.today()
    ago = 10

    date_back = datetime(today.year,today.month,today.day) - timedelta(days=ago)

    print ("looking for %s since %s." % (param_clinic, date_back))

    messages = MessageConfirmation.objects.filter(confirmed=False,
                                                  sent_at__gte=date_back,
                                                  text__icontains=TEST_TYPE)
    for msg in messages:
        req_id = msg.text.split(".")[1].split(":")[-1].strip()

        clinic = msg.connection.contact.location
        if not param_clinic in clinic.name.lower():
            continue

        try:
            res = Result.objects.get(requisition_id=req_id, clinic=clinic,
                                     result_sent_date__gte=date_back)
            res.notification_status = "new"
            res.save()
            msg.confirmed = True
            msg.save()

            print ("cleaned up result %s for clinic %s." % (req_id, clinic.name))
        except (Result.DoesNotExist, Result.MultipleObjectsReturned):
            print ("Failed to find result for unconfirmed printer message"\
                        " : %s, %s, %s" % (msg.id, req_id, clinic.name))
            continue