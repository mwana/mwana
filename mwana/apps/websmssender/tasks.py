# vim: ai ts=4 sts=4 et sw=4
from datetime import date
import logging

from mwana.apps.email.sender import EmailSender
from mwana.apps.issuetracking.utils import get_admin_email_address
from mwana.apps.reports.webreports.models import GroupUserMapping
from mwana.apps.websmssender.models import WebSMSLog

logger = logging.getLogger(__name__)

_ = lambda s: s


def send_webblaster_report(router):

    subject = "Web Blaster Report - %s" % (date.today().strftime("%Y-%m-%d"))

    header = subject

    footer = """
--------------------------------------------------------------------------------
Do not reply. This is a system generated message.
--------------------------------------------------------------------------------

Thank you,
%(admin)s""" % ({'admin':get_admin_email_address()})

    body_template = """
Date Sent: %(date_sent)s
Sender: %(sender)s
Recipents' Group: %(workertype)s
Recipients' Location: %(location)s
# of Recipients: %(recipients_count)s
Message:
%(message)s
-------------------------------------------------------------------------------
"""

    logs = []

    for log in WebSMSLog.objects.exclude(admins_notified=True).order_by('pk')[:30]:
        logs.append(body_template % ({'date_sent': log.date_sent,
                    'sender': log.sender, 'message': log.message,
                    'workertype': log.workertype, 'location': log.location if log.location else "Not Specified" ,
                    'recipients_count': log.recipients_count
                    }))
        log.admins_notified = True
        log.save()

    if not logs:
        return
    
    body = "\n".join(msg for msg in logs)

    recipients=[]
    support_group=GroupUserMapping.objects.filter(group__name__icontains='support',
    user__is_active=True, user__email__icontains='@')

    email_sender=EmailSender()

    for sg in support_group:
        recipients.append(sg.user.email)



    message = ("%s\n%s\n%s" % (header, body, footer))

    print message

    email_sender.send(list(set(recipients)), subject, message)

    