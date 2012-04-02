from mwana.apps.reports.webreports.models import GroupUserMapping
from mwana.apps.email.sender import EmailSender

def get_admin_email_address():
    from djappsettings import settings
    try:
        return settings.ADMINS[0][1]
    except:
        return "Mwana Admin."

def send_issue_email(issue, user):
    edit_mode = "created" if issue.date_created == issue.edited_on else "edited"
    subject = issue.title[:50] + "..." if len(issue.title) > 50 else issue.title
    message = """
Issue %(id)s-%(title)s- has been %(edit_mode)s by %(user_name)s (%(first_name)s %(last_name)s)

Assigned to: %(assigned_to)s
Description:
%(body)s

--------------------------------------------------------------------------------
You are receiving this message because of either of the following:
1) You belong to the Mwana Support Group, or
2) You created a task, or
3) A task has been assigned to you.
--------------------------------------------------------------------------------


--------------------------------------------------------------------------------
Do not reply. This is a system generated message.
--------------------------------------------------------------------------------

Thank you,
%(admin)s
""" % ({'id':issue.id, 'title':issue.title, 'edit_mode':edit_mode,
        'user_name':user.username, 'first_name':user.first_name,
        'last_name':user.last_name,
        'assigned_to':"%s (%s %s)" % (issue.assigned_to.username,
        issue.assigned_to.first_name, issue.assigned_to.last_name),
        'body':issue.body,
        'admin':get_admin_email_address(),
        })

    recipients = []
    support_group = GroupUserMapping.objects.filter(group__name__icontains='support',
    user__is_active=True, user__email__icontains='@').exclude(user=user)

    email_sender = EmailSender()

    for sg in support_group:
#        email_sender.send(sg.user.email, message)
        recipients.append(sg.user)

    if user.email and '@' in user.email:
#        email_sender.send(user.email, message)
        recipients.append(user.email)

    if issue.assigned_to.email and issue.assigned_to.email not in recipients:
        recipients.append(issue.assigned_to.email)
#        email_sender.send(issue.assigned_to.email, message)

    email_sender.send(recipients, subject, message)