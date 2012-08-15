# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.issuetracking.issuehelper import IssueHelper
from mwana.apps.issuetracking.utils import send_issue_email
import logging
from django.contrib.csrf.middleware import csrf_response_exempt, csrf_view_exempt
from django.shortcuts import render_to_response
from django.template import RequestContext
from mwana.apps.alerts.views import get_int
from mwana.apps.issuetracking.forms import IssueForm
from mwana.apps.issuetracking.models import Issue
from mwana.apps.reports.views import read_request



def get_int(val):
    return int(val) if str(val).isdigit() else None

def get_default_int(val):
    return int(val) if str(val).isdigit() else 0



def get_next_navigation(text):
    try:
        return {"Next":1, "Previous":-1}[text]
    except:
        return 0


#def edit_issue(request):
#    issue = Issue()
#    id = None
#    try:
#        issue = Issue.objects.get(pk=id)
#    except Issue.DoesNotExist:
#        pass
#    CommentInlineFormSet = inlineformset_factory(Issue, Comment)
#    if request.method == "POST":
#        formset = CommentInlineFormSet(request.POST, request.FILES, instance=issue)
#        if formset.is_valid():
#            formset.save(commit=False)
#            # Do something.
#    else:
#        formset = CommentInlineFormSet(instance=issue)
#    return render_to_response('issues/edit.html', {
#                              "formset": formset,
#                              })

    
@csrf_response_exempt
@csrf_view_exempt
def list_issues(request):

    
    message = ""
    errors = ""
    navigation = read_request(request, "navigate")
    page = read_request(request, "page")

    page = get_default_int(page)
    page = page + get_next_navigation(navigation)
    
    form = IssueForm() # An unbound form
    if request.method == 'POST': # If the form has been submitted...
        form = IssueForm(request.POST) # A form bound to the POST data
        if form.is_valid():
            type = form.cleaned_data['type']
            status = form.cleaned_data['status']
            priority = form.cleaned_data['priority']
            title = form.cleaned_data['title']
            body = form.cleaned_data['body']
            desired_start_date = form.cleaned_data['desired_start_date']
            desired_completion_date = form.cleaned_data['desired_completion_date']

            web_author = request.user
            open = None
            if status in ['new', 'ongoing', 'resurfaced', 'future']:
                open = True
            elif instance.status in ['completed', 'bugfixed', 'obsolete', 'closed']:
                open = False

            issue = Issue(type=type, status=status, priority=priority, title=title,
            body=body, desired_start_date=desired_start_date, open=open,
            desired_completion_date=desired_completion_date, web_author=web_author)

            issue.save()
            
            message = "Issue has been created: %s" % issue

            if request.user:
                try:
                    send_issue_email(issue, request.user)
                except Exception, e:
                    logger = logging.getLogger(__name__)
                    logger.error(e)

            form = IssueForm() # An unbound form
        else:
            errors = form.errors

    
    
    issueHelper = IssueHelper()

    (issues, num_pages, number, has_next, has_previous) = issueHelper.get_issues(page)
    

    return render_to_response('issues/issues.html',
                              {
                              'issue': form,
                              'message': message,
                              'errors': errors,
                              'issues': issues,
                              'num_pages': num_pages,
                              'number': number,
                              'has_next': has_next,
                              'has_previous': has_previous,
                              }, context_instance=RequestContext(request)
                              )



