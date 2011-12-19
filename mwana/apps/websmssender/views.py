# vim: ai ts=4 sts=4 et sw=4
from datetime import datetime

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.http import require_GET
from mwana.apps.reports.utils.htmlhelper import get_contacttype_dropdown_html
from mwana.apps.reports.utils.htmlhelper import get_contacttypes
from mwana.apps.reports.utils.htmlhelper import get_facilities_dropdown_html
from mwana.apps.reports.utils.htmlhelper import get_facilities_dropdown_htmlb
from mwana.apps.reports.utils.htmlhelper import get_facility_name
from mwana.apps.reports.utils.htmlhelper import get_groups_dropdown_html
from mwana.apps.reports.utils.htmlhelper import get_groups_name
from mwana.apps.reports.utils.facilityfilter import get_rpt_districts
from mwana.apps.reports.utils.facilityfilter import get_rpt_provinces
from mwana.apps.reports.utils.facilityfilter import get_rpt_facilities
from mwana.apps.reports.views import read_request
from mwana.apps.websmssender.smssender import SMSSender

@require_GET
def send_sms(request):

    today = datetime.today().date()
    
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
    phone_pattern = read_request(request, "phone_pattern")
    message = read_request(request, "message")
    meta_infor = ""

    if not (message and message.strip()):
        meta_infor = "Please supply a meesage to send"
    elif len(message) > 160:
        meta_infor = "Please enter a meesage not exceeding 160 characters long"
    else:
        contact_types = get_contacttypes(worker_types)
        sender = SMSSender(current_user=request.user, group=rpt_group, province=rpt_provinces,
                           district=rpt_districts, facility=rpt_facilities,
                           message=message,worker_types=contact_types,
                           phone_pattern=phone_pattern)

        count = sender.send_sms()
        meta_infor = "Your message is being sent to %s users" % count
#    (table, messages_paginator_num_pages, messages_number, messages_has_next, messages_has_previous) = log.get_filtered_message_logs(startdate, enddate, search_key, page)
    

    return render_to_response('websmssender/sendsms.html',
                              {
                              
                              'today': today,

                              'formattedtoday': today.strftime("%d %b %Y"),
                              'formattedtime': datetime.today().strftime("%I:%M %p"),

                              
                              'meta_infor': meta_infor,
                              'message': message if message else "",
                              'phone_pattern': phone_pattern if phone_pattern else "",
                              'is_report_admin': is_report_admin,
                              'region_selectable': True,
                              'implementer': get_groups_name(rpt_group),
                              'province': get_facility_name(rpt_provinces),
                              'district': get_facility_name(rpt_districts),
                              'worker_types': get_contacttype_dropdown_html('worker_types',worker_types),
                              'rpt_group': get_groups_dropdown_html('rpt_group', rpt_group),
                              'rpt_provinces': get_facilities_dropdown_html("rpt_provinces", get_rpt_provinces(request.user), rpt_provinces),
                              'rpt_districts': get_facilities_dropdown_html("rpt_districts", get_rpt_districts(request.user), rpt_districts),
                              'rpt_facilities': get_facilities_dropdown_html("rpt_facilities", get_rpt_facilities(request.user), rpt_facilities),
                              }, context_instance=RequestContext(request)
                              )
