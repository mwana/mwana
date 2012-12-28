# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.reports.webreports.models import ReportingGroup
from datetime import datetime

from django.shortcuts import render_to_response
from django.template import RequestContext
from mwana.apps.blacklist.views import get_default_int
from mwana.apps.reports.utils.htmlhelper import get_default_int
from mwana.apps.reports.utils.htmlhelper import get_facilities_dropdown_html
from mwana.apps.reports.utils.htmlhelper import get_next_navigation
from mwana.apps.reports.views import read_request
from mwana.apps.webusers.webuserservice import WebUserService
from mwana.apps.reports.utils.htmlhelper import get_facility_name
from mwana.apps.reports.utils.htmlhelper import get_groups_dropdown_html
from mwana.apps.reports.utils.htmlhelper import *








    

def webusers(request):

    #TODO enable filter by province and district
    navigation = read_request(request, "navigate")
    page = read_request(request, "page")

    page = get_default_int(page)
    page = page + get_next_navigation(navigation)
    
    
    rpt_group = read_request(request, "rpt_group")
    rpt_provinces = read_request(request, "rpt_provinces")
    rpt_districts = read_request(request, "rpt_districts")
    rpt_facilities = read_request(request, "rpt_facilities")
    
    
    webuserservice = WebUserService()
    (items, num_pages, number, has_next, has_previous, max_per_page) = webuserservice.get_web_users(request.user,
    page, rpt_group, rpt_districts, rpt_provinces)

    records = []
    dynamic_object = None
    
    for record in sorted(items, key=lambda item:item.last_login):
        dynamic_object = record
        dynamic_object.days_ago = (datetime.now() - record.last_login).days
        records.append(record)
        
        
    offset = max_per_page * (number - 1)
    
    groups = ReportingGroup.objects.filter(groupusermapping__user=
                                                    request.user).distinct()
    rpt_group = groups[0] if groups else None

    is_report_admin = False
    try:
        user_group_name = request.user.groupusermapping_set.all()[0].group.name
        if request.user.groupusermapping_set.all()[0].group.id in (1,2)\
        and ("moh" in user_group_name.lower() or "support" in user_group_name.lower()):
            is_report_admin = True
    except:
        pass

    

    return render_to_response('webusers/webusers.html',
                              {
                              'records': records,
                              'region_selectable': True,
                              'offset': offset,
                              'num_pages': num_pages,
                              'number': number,
                              'has_next': has_next,
                              'has_previous': has_previous,

                              'implementer': get_groups_name(rpt_group),
                              'province': get_facility_name(rpt_provinces),
                              'district': get_facility_name(rpt_districts),

                              'is_report_admin': is_report_admin,
                              'region_selectable': True,
                              'rpt_group': get_groups_dropdown_html('rpt_group', rpt_group),
                              'rpt_provinces': get_facilities_dropdown_html("rpt_provinces", get_rpt_provinces(request.user), rpt_provinces),
                              'rpt_districts': get_facilities_dropdown_html("rpt_districts", get_rpt_districts(request.user), rpt_districts),
                              'rpt_facilities': get_facilities_dropdown_html("rpt_facilities", get_rpt_facilities(request.user), rpt_facilities),
                              }, context_instance=RequestContext(request)
                              )



