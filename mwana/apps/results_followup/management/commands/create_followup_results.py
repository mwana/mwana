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
from django.contrib.auth.models import Group
from django.contrib.auth.models import User


class Command(LabelCommand):
    help = "Populate/update InfantResultAlert data"
    args = ""
    
    def handle(self, * args, ** options):
        update_infant_result_alert()
                
    def __del__(self):
        pass


def update_permissions():
    group, _ = Group.objects.get_or_create(name='Results Followup')
    for manager in EmailRecipientForInfantResultAlert.objects.filter(is_active=True, user__email__contains='@'):
        if group not in manager.user.groups.all():
            print 'adding permissions for', manager, ' to ', group
            group.user_set.add(manager.user)


def update_infant_result_alert():
    """
    
    """
    #TODO: write, unit test, task, frontend

    update_permissions()

    lookback_date = date.today() - timedelta(days=150)

    results = Result.objects.filter(result='P').exclude(processed_on__lte=lookback_date).\
        exclude(arrival_date__lte=lookback_date).exclude(clinic=None)

    for res in results:
        obj, created = InfantResultAlert.objects.get_or_create(result=res)
        if not created:
            obj.save()

    alerts = InfantResultAlert.objects.filter(notification_status__in=['new', 'notified'])
    alerted = []
    if not alerts:
        print 'No alerts'
        return
    email_sender = EmailSender()
    date_back = date.today() - timedelta(days=31)

    for manager in EmailRecipientForInfantResultAlert.objects.filter(is_active=True, user__email__contains='@').\
            exclude(last_alert_date__gte=date_back):
        facs = Location.objects.filter(groupfacilitymapping__group__groupusermapping__user=manager.user)
        manager_alerts = alerts.filter(location__in=facs)
        if not manager_alerts:
            print 'No alerts for', manager.user.username
            continue
        message_text = ('Hello %s %s, you have %s results that you need to follow up. Follow this link to take action: '
                        '%s/admin/results_followup/infantresultalert/') % (manager.user.first_name,
                                                                           manager.user.last_name,
                                                                           len(manager_alerts), settings.SERVER_ADDRESS)

        print "sending mail", manager.user.email, message_text
        email_sender.send(list(set([manager.user.email])), 'ATTENTION: Your follow-up needed', message_text)
        manager.last_alert_number = len(manager_alerts)
        manager.last_alert_date = date.today()
        manager.save()
        for alert in manager_alerts:
            alerted.append(alert)
    for alert in alerted:
        alert.notification_status = 'notified'
        alert.followup_status = 'alerted'
        alert.save()
