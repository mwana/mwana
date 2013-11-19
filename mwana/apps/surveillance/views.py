# vim: ai ts=4 sts=4 et sw=4
import csv
from datetime import date
from datetime import timedelta
import htmlentitydefs as ht
import re

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from mwana.apps.locations.models import Location
from mwana.apps.reports.utils.htmlhelper import get_incident_grid_selector
from mwana.apps.reports.utils.htmlhelper import get_incident_report_html_dropdown
from mwana.apps.reports.utils.htmlhelper import read_date_or_default
from mwana.apps.surveillance.models import Incident
from mwana.apps.surveillance.models import Report
from mwana.apps.surveillance.models import UserIncident
from mwana.const import MWANA_ZAMBIA_START_DATE


def assign_new_indicators(user, ids):
    if not user:
        return

    incidents = Incident.objects.filter(id__in=ids)
    UserIncident.objects.filter(user=user).exclude(incident__in=incidents).delete()
    for incident in incidents:
        UserIncident.objects.get_or_create(user=user, incident=incident)

def htmltable_to_rows(html_table):
    # Found it more satisfactory to do my own implementation.
    # Had trouble having BeautifulSoup to work on local machine. table2CSV.js
    # had shortcomings
    to_return = []
    a = html_table.replace('</td>', '|').replace('</th>', '|').replace('</tr>', '\n')    
    c = re.sub('<.*?>', '', a)
    for k, v in ht.name2codepoint.items():
        c = c.replace("&%s;" % k, unichr(int(v)))
    
    for t in c.split('\n'):
        to_return.append(t.split('|')[:-1])
    return to_return

def export_to_csv(request):
    file_name = dict(request.REQUEST).get('filename') or "somefilename.csv"
    data = dict(request.REQUEST).get('csv_text') or ""    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s"' % file_name

    writer = csv.writer(response, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    
    for row in htmltable_to_rows(data):
        writer.writerow(row)
        
    return response

def surveillance(request):
    today = date.today()
    try:
        update_user_incidents = request.POST['update_user_incidents']
        if update_user_incidents and update_user_incidents == 'True':
            assign_new_indicators(request.user, map(int, dict(request.POST)["_select_case"]))
    except KeyError:
        pass

    startdate1 = read_date_or_default(request, 'startdate', today - timedelta(days=30))
    enddate1 = read_date_or_default(request, 'enddate', today)
    start_date = min(startdate1, enddate1, date.today())
    end_date = min(max(enddate1, MWANA_ZAMBIA_START_DATE), date.today())

    districts = [str(loc.slug) for loc in Location.objects.filter(type__slug='districts', location__supportedlocation__supported=True).distinct()]
    provinces = [str(loc.slug) for loc in Location.objects.filter(type__slug='provinces', location__location__supportedlocation__supported=True).distinct()]
    cases = Incident.objects.all().exclude(report=None)
    # if user is None all incidents/cases will be returned
    user_incidents = cases.filter(userincident__user=request.user)
    group_incidents = cases.filter(groupincident__group__groupusermapping__user=request.user)
    my_incidents = (user_incidents | group_incidents).distinct()
    reports = Report.objects.filter(date__gte=start_date, date__lte=end_date, incident__in=my_incidents)
    a = reports.filter(value__gte=6).order_by('-date', '-value').values_list('incident')
    selected_id = a[0][0] if a else ""
    user_name = request.user or "I"

    return render_to_response('surveillance/surveillance.html',
                              {
                              "fstart_date": start_date.strftime("%Y-%m-%d"),
                              "fend_date": end_date.strftime("%Y-%m-%d"),
                              "cases1": get_incident_report_html_dropdown('cases1', my_incidents, selected_id, False),
                              "cases2": get_incident_report_html_dropdown('cases2', my_incidents, ""),
                              "cases3": get_incident_report_html_dropdown('cases3', my_incidents, ""),
                              "cases4": get_incident_report_html_dropdown('cases4', my_incidents, ""),
                              "cases5": get_incident_report_html_dropdown('cases5', my_incidents, ""),
                              "districts": districts,
                              "provinces": provinces,
                              "reports": reports,
                              "user_name": user_name,
                              "incident_grid_select": get_incident_grid_selector(id, cases, my_incidents, 2)
                              }, context_instance=RequestContext(request)
                              )