# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.reports.webreports.models import GroupUserMapping
from datetime import timedelta
from mwana.apps.email.sender import EmailSender


def get_admin_email_address():
    from djappsettings import settings
    try:
        return settings.ADMINS[0][1]
    except:
        return "Mwana Admin."


def send_issue_email(issue, user):
    edit_mode = "created" if (issue.edited_on - issue.date_created) < timedelta(seconds=10)  else "edited"
    subject = issue.title[:50] + "..." if len(issue.title) > 50 else issue.title
    message = """
Issue %(id)s-%(title)s- has been %(edit_mode)s by %(user_name)s (%(first_name)s %(last_name)s)

Priority: %(priority)s
Type: %(type)s
Status: %(status)s
Assigned to: %(assigned_to)s
Desired Start Date: %(desired_start_date)s. Desired End Date: %(desired_completion_date)s
Development time: %(dev_time)s
Percent Complete: %(perc_complete)s
Description:
%(body)s

%(comments)s

Thank you,
%(admin)s

----------------------------------------------
Do not reply. This is a system generated message.
----------------------------------------------
You are receiving this message because of either of the following:
1) You belong to the Mwana Support Group, or
2) You created a task, or
3) A task has been assigned to you.
----------------------------------------------
""" % ({'id':issue.id, 'title':issue.title, 'edit_mode':edit_mode,
        'user_name':user.username, 'first_name':user.first_name,
        'last_name':user.last_name,
        'assigned_to':"%s (%s %s)" % (
        issue.assigned_to.username if issue.assigned_to else "",
        issue.assigned_to.first_name if issue.assigned_to else "",
        issue.assigned_to.last_name if issue.assigned_to else ""),
        'status':issue.get_status_display(),
        'priority':issue.get_priority_display(),
        'type':issue.get_type_display(),
        'perc_complete':issue.get_percentage_complete_display(),
        'dev_time':issue.dev_time,
        'desired_start_date':issue.desired_start_date.strftime('%d/%m/%Y')\
        if issue.desired_start_date else "",
        'desired_completion_date':issue.desired_completion_date.strftime(
        '%d/%m/%Y') if issue.desired_completion_date else "",
        'body':issue.body,
        'admin':get_admin_email_address(),
        'comments': ('-' * 80).join( "\nComment on %s\n%s\n" % (comment.edited_on,
        comment.body) for comment in issue.comment_set.all())
        })

    recipients = []
    support_group = GroupUserMapping.objects.filter(group__name__icontains='support',
    user__is_active=True, user__email__icontains='@').exclude(user=user)

    email_sender = EmailSender()

    for sg in support_group:
        recipients.append(sg.user.email)

    if user.email and '@' in user.email:
        recipients.append(user.email)

    if issue.assigned_to and issue.assigned_to.email \
    and issue.assigned_to.email not in recipients:
        recipients.append(issue.assigned_to.email)

    email_sender.send(list(set(recipients)), subject, message)


def send_comment_email(comment):
    issue = comment.issue

    subject = comment.body[:50] + "..." if len(comment.body) > 50 else comment.body
    issue_title = issue.title[:50] + "..." if len(issue.title) > 50 else issue.title
    message = """
A comment has been added to issue %(issue_id)s - %(issue_title)s

Comment Text:
%(comment)s


--------------------------------------------------------------------------------
Do not reply. This is a system generated message.
--------------------------------------------------------------------------------

Thank you,
%(admin)s
""" % ({'issue_id':issue.id, 'issue_title':issue_title,
        'admin':get_admin_email_address(),'comment':comment.body,})

    recipients = []
    support_group = GroupUserMapping.objects.filter(group__name__icontains='support',
    user__is_active=True, user__email__icontains='@')

    email_sender = EmailSender()

    for sg in support_group:
        recipients.append(sg.user.email)

    

    if issue.assigned_to and issue.assigned_to.email \
    and issue.assigned_to.email not in recipients:
        recipients.append(issue.assigned_to.email)

    email_sender.send(list(set(recipients)), subject, message)