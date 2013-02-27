# vim: ai ts=4 sts=4 et sw=4
from datetime import datetime
from datetime import timedelta

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.http import require_GET
from mwana.apps.reports.utils.htmlhelper import get_contacttypes
from mwana.apps.reports.utils.htmlhelper import get_contacttype_dropdown_html
from mwana.apps.alerts.views import get_int
from mwana.apps.filteredlogs.messagefilter import MessageFilter
from mwana.apps.reports.utils.htmlhelper import get_facilities_dropdown_html
from mwana.apps.reports.views import get_groups_dropdown_html
from mwana.apps.reports.views import read_request
from mwana.apps.reports.views import text_date
from mwana.apps.reports.views import try_format
from mwana.apps.reports.webreports.models import ReportingGroup
from mwana.apps.locations.models import Location



def get_int(val):
    return int(val) if str(val).isdigit() else None

def get_default_int(val):
    return int(val) if str(val).isdigit() else 0

def get_groups_name(id):
    try:
        return ReportingGroup.objects.get(pk=id)
    except:
        return "All"

def get_facility_name(slug):
    try:
        return Location.objects.get(slug=slug)
    except:
        return "All"

def get_next_navigation(text):
    try:
        return {"Next":1,"Previous":-1}[text]
    except:
        return 0

@require_GET
def filtered_logs(request):    

    today = datetime.today().date()
    try:
        startdate1 = text_date(request.REQUEST['startdate'])
    except (KeyError, ValueError, IndexError):
        startdate1 = today - timedelta(days=1)

    try:
        enddate1 = text_date(request.REQUEST['enddate'])
    except (KeyError, ValueError, IndexError):
        enddate1 = datetime.today().date()
    startdate = min(startdate1, enddate1, datetime.today().date())
    enddate = min(max(enddate1, startdate1), datetime.today().date())

    is_report_admin = False
    try:
        user_group_name = request.user.groupusermapping_set.all()[0].group.name
        if request.user.groupusermapping_set.all()[0].group.id in (1, 2)\
        and ("moh" in user_group_name.lower() or "support" in user_group_name.lower()):
            is_report_admin = True
    except:
        pass

    rpt_group = read_request(request, "rpt_group")
    rpt_provinces = read_request(request, "rpt_provinces")
    rpt_districts = read_request(request, "rpt_districts")
    rpt_facilities = read_request(request, "rpt_facilities")
    worker_types = read_request(request, "worker_types")
    search_key = read_request(request, "search_key")
    navigation = read_request(request, "navigate")
    page = read_request(request, "page")

    page = get_default_int(page)
    page = page + get_next_navigation(navigation)
    

    log = MessageFilter(request.user, rpt_group, rpt_provinces, rpt_districts, rpt_facilities, get_contacttypes(worker_types, True))

    (table, messages_paginator_num_pages, messages_number, messages_has_next, messages_has_previous) = log.get_filtered_message_logs(startdate, enddate, search_key, page)
    

    return render_to_response('messagelogs/messages.html',
                              {'startdate': startdate,
                              'enddate': enddate,
                              'fstartdate': try_format(startdate),
                              'fenddate': try_format(enddate),
                              'today': today,

                              'formattedtoday': today.strftime("%d %b %Y"),
                              'formattedtime': datetime.today().strftime("%I:%M %p"),

                              
                              'messages':table,
                              "messages_paginator_num_pages":  messages_paginator_num_pages,
                              "messages_number":  messages_number,
                              "messages_has_next":  messages_has_next,
                              "messages_has_previous":  messages_has_previous,
                              'is_report_admin': is_report_admin,
                              'region_selectable': True,
                              'implementer': get_groups_name(rpt_group),
                              'province': get_facility_name(rpt_provinces),
                              'district': get_facility_name(rpt_districts),
                              'worker_types': get_contacttype_dropdown_html('worker_types',worker_types, True),
                              'rpt_group': get_groups_dropdown_html('rpt_group', rpt_group),
                              'rpt_provinces': get_facilities_dropdown_html("rpt_provinces", log.get_rpt_provinces(request.user), rpt_provinces),
                              'rpt_districts': get_facilities_dropdown_html("rpt_districts", log.get_rpt_districts(request.user), rpt_districts),
                              'rpt_facilities': get_facilities_dropdown_html("rpt_facilities", log.get_rpt_facilities(request.user), rpt_facilities),
                              'search_key': search_key if search_key else ""
                              }, context_instance=RequestContext(request)
                              )
