# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.blacklist.views import get_default_int
from mwana.apps.webusers.webuserservice import WebUserService
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
from mwana.apps.reports.utils.htmlhelper import get_facilities_dropdown_html
from mwana.apps.reports.utils.htmlhelper import get_next_navigation
from mwana.apps.reports.utils.htmlhelper import get_default_int
from datetime import datetime








    

def webusers(request):

    
    navigation = read_request(request, "navigate")
    page = read_request(request, "page")

    page = get_default_int(page)
    page = page + get_next_navigation(navigation)
    
    

    
    
    webuserservice = WebUserService()
    (items, num_pages, number, has_next, has_previous, max_per_page) = webuserservice.get_web_users(request.user, page)

    records = []
    dynamic_object = None
    
    for record in sorted(items, key=lambda item:item.last_login):
        dynamic_object = record
        dynamic_object.days_ago = (datetime.now() - record.last_login).days
        records.append(record)
        
        
    offset = max_per_page * (number - 1)

    return render_to_response('webusers/webusers.html',
                              {                            
                              'records': records,
                              'offset': offset,
                              'num_pages': num_pages,
                              'number': number,
                              'has_next': has_next,
                              'has_previous': has_previous,
                              }, context_instance=RequestContext(request)
                              )



