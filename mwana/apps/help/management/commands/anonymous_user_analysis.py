# vim: ai ts=4 sts=4 et sw=4
"""
Lists formerly registerd users who are now requesting for help.
"""

from datetime import datetime
from datetime import timedelta

from django.core.management.base import LabelCommand
from django.core.management.base import CommandError
from mwana.util import get_clinic_or_default
from mwana.apps.help.models import HelpRequest
from rapidsms.contrib.messagelog.models import Message


class Command(LabelCommand):
    help = "Lists formerly registerd users who are now requesting for help."
    args = "<lookback (days)>"
    label = 'number of days to lookback'

    def handle(self, * args, ** options):
        if len(args) < 1:
            raise CommandError('Please specify %s.' % self.label)
        look_back = int((args[0]))
        process_helps(look_back)

        
def process_helps(look_back):
    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    date_back = today - timedelta(days=look_back)

    help_requests = HelpRequest.objects.filter(requested_on__gte=date_back, requested_by__contact=None)


    for help_request in help_requests:
        # @type help_request HelpRequest
        msgs = Message.objects.filter(connection=help_request.requested_by).\
        exclude(date__lte=help_request.requested_on).\
        exclude(contact=None).exclude(contact__location__name='Training Clinic').\
        exclude(contact__location__parent__name='Training Clinic').\
        exclude(contact__location__name='Training District').\
        exclude(contact__location__name='Training Province')
        found  = []
        for msg in msgs:
            if msg.connection not in found:
                if msg.contact.is_active:
                    continue
                found.append(msg.connection)
                print "|".join(str(i) for i in [msg.contact, msg.connection, get_clinic_or_default(msg.contact).slug, get_clinic_or_default(msg.contact), msg.contact.location, msg.contact.location.parent])


    def __del__(self):
        pass
