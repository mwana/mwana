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
    confirmed = read_request(request, "confirmed")
    cancel = read_request(request, "cancel")
    meta_infor = ""
    get_only_select = False

    confirm_message = ""
    recipients_count, facs_count = 0, 0
    
    if (cancel == "Cancel"):
        confirmed = "no"
        message = ""
    elif not (message and message.strip()):
        meta_infor = "Please supply a message to send"
    elif len(message) > 160:
        meta_infor = "Please enter a message not exceeding 160 characters long"
    else:
        contact_types = get_contacttypes(worker_types)
        sender = SMSSender(current_user=request.user, group=rpt_group, province=rpt_provinces,
                           district=rpt_districts, facility=rpt_facilities,
                           message=message,worker_types=contact_types,
                           phone_pattern=phone_pattern)

        if confirmed == 'yes':
            count = sender.send_sms()
            confirmed = "no"
            meta_infor = "Your message is being sent to %s users" % count

        else:
            get_only_select = True
            recipients_count, facs_count = sender.count_of_recipients()
            confirm_message = ("You are about to send your message to a total of %s \
            recipients from %s different facilities. Click Ok to continue or\
            Cancel to quit." % (recipients_count, facs_count))
            confirmed = "yes"

        


    return render_to_response('websmssender/sendsms.html',
                              {
                              
                              'today': today,

                              'formattedtoday': today.strftime("%d %b %Y"),
                              'formattedtime': datetime.today().strftime("%I:%M %p"),

                              
                              'confirm_message': confirm_message,
                              'confirmed': confirmed,
                              'recipients_count': recipients_count,
                              'facs_count': facs_count,
                              'meta_infor': meta_infor,
                              'message': message if message else "",
                              'phone_pattern': phone_pattern if phone_pattern else "",
                              'is_report_admin': is_report_admin,
                              'implementer': get_groups_name(rpt_group),
                              'province': get_facility_name(rpt_provinces),
                              'district': get_facility_name(rpt_districts),
                              'worker_types': get_contacttype_dropdown_html('worker_types',worker_types),
                              'rpt_group': get_groups_dropdown_html('rpt_group', rpt_group),
                              'rpt_provinces': get_facilities_dropdown_html("rpt_provinces", get_rpt_provinces(request.user), rpt_provinces, get_only_select),
                              'rpt_districts': get_facilities_dropdown_html("rpt_districts", get_rpt_districts(request.user), rpt_districts, get_only_select),
                              'rpt_facilities': get_facilities_dropdown_html("rpt_facilities", get_rpt_facilities(request.user), rpt_facilities, get_only_select),
                              }, context_instance=RequestContext(request)
                              )
