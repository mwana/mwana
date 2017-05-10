# vim: ai ts=4 sts=4 et sw=4
"""

"""
from datetime import date, timedelta

from django.core.management.base import LabelCommand

from mwana.apps.email.sender import EmailSender
from mwana.apps.locations.models import Location
from mwana.apps.results_followup.models import EmailRecipientForInfantResultAlert

from mwana.apps.labresults.models import Result
from mwana.apps.results_followup.models import InfantResultAlert
from django.conf import settings


class Command(LabelCommand):
    help = "Populate/update InfantResultAlert data"
    args = ""
    
    def handle(self, * args, ** options):
        update_infant_result_alert()
                
    def __del__(self):
        pass


def update_infant_result_alert():
    """
    For testing purposes
    :return: None
    """
    #TODO: write proper implementation

    lookback_date = date.today() - timedelta(days=60)

    results = Result.objects.filter(result='P').exclude(processed_on__lte=lookback_date).\
        exclude(arrival_date__lte=lookback_date).exclude(clinic=None)

    for res in results:
        obj, created = InfantResultAlert.objects.get_or_create(result=res)
        if not created:
            obj.save()

    alerts = InfantResultAlert.objects.filter(notification_status='new')
    if not alerts:
        return
    email_sender = EmailSender()
    for manager in EmailRecipientForInfantResultAlert.objects.filter(user__email__contains='@'):
        manager_alerts = alerts.filter(location__in=Location.objects.filter(groupfacilitymapping__group__in=
                                                                            manager.user.groupusermapping_set.all()))
        if not manager_alerts:
            continue
        message_text = ('Hello %s %s, you have %s results that you need to follow up. Follow this link to take action: '
                        '%s/admin/results_followup/infantresultalert/') % (manager.user.first_name,
                                                                           manager.user.last_name,
                                                                           len(manager_alerts), settings.SERVER_ADDRESS)

        print "sending mail", manager.user.email, message_text
        email_sender.send(list(set(manager.user.email)), 'ATTENTION: Your follow-up needed', message_text)
