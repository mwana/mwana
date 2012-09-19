# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.reports.models import Login
from datetime import datetime, timedelta, date

from django.views.decorators.http import require_GET
from django.template import RequestContext
from django.shortcuts import render_to_response
from mwana.apps.reports.webreports.models import ReportingGroup
from mwana.apps.reports.utils.htmlhelper import get_facilities_dropdown_html
from django.shortcuts import redirect
from django.contrib.auth.models import User





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

def text_date(text):
    delimiters = ('-', '/')
    for delim in delimiters:
        text = text.replace(delim, ' ')
    a, b, c = text.split()
    if len(a) == 4:
        return date(int(a), int(b), int(c))
    else:
        return date(int(c), int(b), int(a))


@require_GET
def malawi_reports(request, location=None):
    from webreports.reportcreator import MalawiReports

    today = datetime.today().date()
    try:
        startdate1 = text_date(request.REQUEST['startdate'])
    except (KeyError, ValueError, IndexError):
        startdate1 = today - timedelta(days=30)

    try:
        enddate1 = text_date(request.REQUEST['enddate'])
    except (KeyError, ValueError, IndexError):
        enddate1 = datetime.today().date()
    startdate = min(startdate1, enddate1, datetime.today().date())
    enddate = min(max(enddate1, startdate1), datetime.today().date())

    try:
        district = request.REQUEST['location']
    except (KeyError, ValueError, IndexError):
        district = "All Districts"

    r = MalawiReports()
    res = r.dbsr_tested_retrieved_report(startdate, enddate, district)

    min_turnaround_time, max_turnaround_time, num_of_rsts, num_of_facilities,\
    turnaround_time = r.dbs_avg_turnaround_time_report(startdate, enddate)

    pending = r.dbsr_pending_results_report(startdate, enddate, district)

    districts = r.get_live_districts()

    births = r.reminders_patient_events_report(startdate, enddate)

    single_bar_length, tt_in_graph, \
    graph = r.dbsr_graph_data(startdate, enddate, district)

    total_dbs, percent_positive_district, percent_negative_district, \
    percent_rejected_district= r.dbsr_positivity_data(startdate, enddate, district)

    return render_to_response('reports/malawi.html',
        {'startdate': startdate,
         'enddate': enddate,
         'today': today,
         'sent_results_rpt': res,
         'districts': districts,
         'selected_location': district,
         'turnaround_time_rpt': turnaround_time,
         'min_turnaround_time': min_turnaround_time,
         'max_turnaround_time': max_turnaround_time,
         'num_of_results': num_of_rsts,
         'num_of_facilities': num_of_facilities,
         'births_rpt': births,
         'formattedtoday': today.strftime("%d %b %Y"),
         'formattedtime': datetime.today().strftime("%I:%M %p"),
         'graph': graph,
         'single_bar_length': single_bar_length,
         'tt_in_graph': tt_in_graph,
         'pending_results': pending,
         'percent_positive_district': percent_positive_district,
         'percent_negative_district': percent_negative_district,
         'percent_rejected_district': percent_rejected_district,
         'total_dbs': total_dbs,
     }, context_instance=RequestContext(request))


#def get_facilities_dropdown_html(id, facilities, selected_facility):
#    #TODO: move this implemention to templates
#    code ='<select name="%s" size="1">\n'%id
#    code +='<option value="All">All</option>\n'
#    if not facilities:
#        return '<select name="%s" size="1"></select>\n'%id
#
#    for fac in facilities:
#        if fac.slug == selected_facility:
#            code = code + '<option selected value="%s">%s</option>\n'%(fac.slug,fac.name)
#        else:
#            code = code + '<option value="%s">%s</option>\n'%(fac.slug,fac.name)
#
#    code = code +'</select>'
#    return code

def get_groups_dropdown_html(id, selected_group):
    #TODO: move this implemention to templates
    code ='<select name="%s" size="1">\n'%id
    code +='<option value="All">All</option>\n'
    for group in ReportingGroup.objects.all():
        if str(group.id) == selected_group:
            code = code + '<option selected value="%s">%s</option>\n'%(group.id,group.name)
        else:
            code = code + '<option value="%s">%s</option>\n'%(group.id,group.name)

    code = code +'</select>'
    return code

def read_request(request,param):
    try:
        value = request.REQUEST[param].strip()
        if value =='All':
            value = None
    except:
        value = None
    return value

def try_format(date):
    try:
        return date.strftime("%Y-%m-%d")
    except:
        return date

def get_admin_email_address():
    from djappsettings import settings
    try:
        return settings.ADMINS[0][1]
    except:
        return "Admin's email address"

@require_GET
def zambia_reports(request):

    if request.user and "dont_check_first_login" \
            not in request.session:
        request.session["dont_check_first_login"] = True

        login = Login.objects.get_or_create(user=request.user)[0]
        if not login.ever_logged_in:
            login.ever_logged_in = True
            login.save()
#            return redirect('/admin/password_change/?post_change_redirect=/')
            return redirect('/admin/password_change')


    from webreports.reportcreator import Results160Reports

    today = datetime.today().date()
    try:
        startdate1 = text_date(request.REQUEST['startdate'])
    except (KeyError, ValueError, IndexError):
        startdate1 = today - timedelta(days=30)

    try:
        enddate1 = text_date(request.REQUEST['enddate'])
    except (KeyError, ValueError, IndexError):
        enddate1 = datetime.today().date()
    startdate = min(startdate1, enddate1, datetime.today().date())
    enddate = min(max(enddate1, startdate1), datetime.today().date())

    is_report_admin = False
    try:
        user_group_name = request.user.groupusermapping_set.all()[0].group.name
        if request.user.groupusermapping_set.all()[0].group.id in (1,2)\
        and ("moh" in user_group_name.lower() or "support" in user_group_name.lower()):
            is_report_admin = True
    except:
        pass
    
    rpt_group = read_request(request, "rpt_group")
    rpt_provinces = read_request(request, "rpt_provinces")
    rpt_districts = read_request(request, "rpt_districts")
    rpt_facilities = read_request(request, "rpt_facilities")
      
    r = Results160Reports(request.user,rpt_group,rpt_provinces,rpt_districts,rpt_facilities)
    res = r.dbs_sent_results_report(startdate, enddate)

    min_processing_time, max_processing_time, num_of_dbs_processed, \
    num_facs_processing, processing_time =\
    r.dbs_avg_processing_time_report(startdate, enddate)

    min_entering_time, max_entering_time, num_of_rsts_entered, \
    num_facs_entering, entering_time =\
    r.dbs_avg_entering_time_report(startdate, enddate)

    min_retrieval_time, max_retrieval_time, num_of_dbs_retrieved, \
    num_facs_retrieving, retrieval_time =\
    r.dbs_avg_retrieval_time_report(startdate, enddate)

    min_turnaround_time, max_turnaround_time, num_of_rsts, num_of_facilities,\
    turnaround_time = r.dbs_avg_turnaround_time_report(startdate, enddate)

    min_transport_time, max_transport_time, num_of_dbs, num_of_facs,\
    transport_time = r.dbs_avg_transport_time_report(startdate, enddate)

    samples_reported = r.dbs_sample_notifications_report(startdate, enddate)

    samples_at_lab = r.dbs_samples_at_lab_report(startdate, enddate)

    pending = r.dbs_pending_results_report(startdate, enddate)

    payloads = r.dbs_payloads_report(startdate, enddate)

    births2 = r.rm_patient_events_report(startdate, enddate)
    births_without_loc = r.rm_patient_events_report_unknown_location(startdate, enddate)

    single_bar_length, tt_in_graph, graph = r.dbs_graph_data(startdate,
                                                             enddate)

    percent_positive_country, percent_negative_country, \
    percent_rejected_country, percent_positive_provinces, \
    percent_negative_provinces, percent_rejected_provinces, total_dbs, \
    months_reporting, days_reporting, year_reporting = r.dbs_positivity_data()

    return render_to_response('reports/zambia.html',
        {'startdate': startdate,
         'enddate': enddate,
         'fstartdate': try_format(startdate),
         'fenddate': try_format(enddate),
         'today': today,
         'adminEmail': get_admin_email_address(),
         'userHasNoAssingedFacilities': False if r.get_rpt_provinces(request.user) else True,
         'sent_results_rpt': res,
         'turnaround_time_rpt': turnaround_time,
         'min_turnaround_time': min_turnaround_time,
         'max_turnaround_time': max_turnaround_time,
         'num_of_results': num_of_rsts,
         'num_of_facilities': num_of_facilities,
         'processing_time_rpt': processing_time,
         'min_processing_time': min_processing_time,
         'max_processing_time': max_processing_time,
         'num_of_dbs_processed': num_of_dbs_processed,
         'num_facs_processing': num_facs_processing,
         'retrieval_time_rpt': retrieval_time,
         'min_retrieving_time': min_retrieval_time,
         'max_retrieving_time': max_retrieval_time,
         'num_of_dbs_retrieved': num_of_dbs_retrieved,
         'num_facs_retrieving': num_facs_retrieving,
         'entering_time_rpt': entering_time,
         'min_entering_time': min_entering_time,
         'max_entering_time': max_entering_time,
         'num_of_rsts_entered': num_of_rsts_entered,
         'num_facs_entering': num_facs_entering,
         'transport_time_rpt': transport_time,
         'min_transport_time': min_transport_time,
         'max_transport_time': max_transport_time,
         'num_of_dbs': num_of_dbs,
         'num_of_facs': num_of_facs,
         'samples_reported_rpt': samples_reported,
         'samples_at_lab_rpt': samples_at_lab,
         'pending_results': pending,
         'payloads_rpt': payloads,         
         'births_rpt2': births2,
         'births_without_loc': births_without_loc,
         'formattedtoday': today.strftime("%d %b %Y"),
         'formattedtime': datetime.today().strftime("%I:%M %p"),
         'graph': graph,
         'single_bar_length': single_bar_length,
         'tt_in_graph': tt_in_graph,
         'percent_positive_country': percent_positive_country,
         'percent_negative_country': percent_negative_country,
         'percent_rejected_country': percent_rejected_country,
         'percent_positive_provinces': percent_positive_provinces,
         'percent_negative_provinces': percent_negative_provinces,
         'percent_rejected_provinces': percent_rejected_provinces,
         'total_dbs': total_dbs,
         'months_reporting': months_reporting,
         'days_reporting': days_reporting,
         'year_reporting': year_reporting,
         'is_report_admin': is_report_admin,
         'region_selectable': True,
         'rpt_group': get_groups_dropdown_html('rpt_group',rpt_group),
         'rpt_provinces': get_facilities_dropdown_html("rpt_provinces", r.get_rpt_provinces(request.user), rpt_provinces) ,
         'rpt_districts': get_facilities_dropdown_html("rpt_districts", r.get_rpt_districts(request.user), rpt_districts) ,
         'rpt_facilities': get_facilities_dropdown_html("rpt_facilities", r.get_rpt_facilities(request.user), rpt_facilities) ,
     }, context_instance=RequestContext(request))

@require_GET
def contacts_report(request):

    from webreports.reportcreator import Results160Reports

    today = datetime.today().date()
    

    is_report_admin = False
    try:
        user_group_name = request.user.groupusermapping_set.all()[0].group.name
        if request.user.groupusermapping_set.all()[0].group.id in (1,2)\
        and ("moh" in user_group_name.lower() or "support" in user_group_name.lower()):
            is_report_admin = True
    except:
        pass

    rpt_group = read_request(request, "rpt_group")
    rpt_provinces = read_request(request, "rpt_provinces")
    rpt_districts = read_request(request, "rpt_districts")
    rpt_facilities = read_request(request, "rpt_facilities")

    r = Results160Reports(request.user,rpt_group,rpt_provinces,rpt_districts,rpt_facilities)
      
    navigation = read_request(request, "navigate")
    page = read_request(request, "page")

    page = get_default_int(page)
    page = page + get_next_navigation(navigation)




    (facility_contacts, messages_paginator_num_pages, messages_number, messages_has_next, messages_has_previous) = r.facility_contacts_report(page)

   
    return render_to_response('reports/contacts.html',
        {
         'today': today,
         'adminEmail': get_admin_email_address(),
         'userHasNoAssingedFacilities': False if r.get_rpt_provinces(request.user) else True,
         'formattedtoday': today.strftime("%d %b %Y"),
         'formattedtime': datetime.today().strftime("%I:%M %p"),
         "messages_paginator_num_pages":  messages_paginator_num_pages,
         "messages_number":  messages_number,
         "messages_has_next":  messages_has_next,
         "messages_has_previous":  messages_has_previous,
         'implementer': get_groups_name(rpt_group),
          'province': get_facility_name(rpt_provinces),
          'district': get_facility_name(rpt_districts),
                              
         'is_report_admin': is_report_admin,
         'region_selectable': True,
         'facility_contacts': facility_contacts,
         'rpt_group': get_groups_dropdown_html('rpt_group',rpt_group),
         'rpt_provinces': get_facilities_dropdown_html("rpt_provinces", r.get_rpt_provinces(request.user), rpt_provinces) ,
         'rpt_districts': get_facilities_dropdown_html("rpt_districts", r.get_rpt_districts(request.user), rpt_districts) ,
         'rpt_facilities': get_facilities_dropdown_html("rpt_facilities", r.get_rpt_facilities(request.user), rpt_facilities) ,
     }, context_instance=RequestContext(request))
