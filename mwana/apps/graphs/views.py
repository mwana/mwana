# vim: ai ts=4 sts=4 et sw=4
from datetime import date
from datetime import timedelta

from django.shortcuts import render_to_response
from django.template import RequestContext
from mwana.apps.graphs.utils import GraphServive
from mwana.apps.reports.utils.htmlhelper import get_facilities_dropdown_html
from mwana.apps.reports.utils.htmlhelper import get_rpt_districts
from mwana.apps.reports.utils.htmlhelper import get_rpt_facilities
from mwana.apps.reports.utils.htmlhelper import get_rpt_provinces
from mwana.apps.reports.utils.htmlhelper import read_date_or_default
from mwana.apps.reports.views import read_request
from mwana.const import MWANA_ZAMBIA_START_DATE


class Expando:
    pass

def graphs(request):
    end_date = date.today()
    start_date = end_date - timedelta(days=30)

    rpt_provinces = read_request(request, "rpt_provinces")
    rpt_districts = read_request(request, "rpt_districts")
    rpt_facilities = read_request(request, "rpt_facilities")
    return render_to_response('graphs/graphs.html',
                              {
                              "fstart_date": start_date.strftime("%Y-%m-%d"),
                              "fend_date": end_date.strftime("%Y-%m-%d"),
                              'rpt_provinces': get_facilities_dropdown_html("rpt_provinces", get_rpt_provinces(request.user), rpt_provinces),
                              'rpt_districts': get_facilities_dropdown_html("rpt_districts", get_rpt_districts(request.user), rpt_districts),
                              'rpt_facilities': get_facilities_dropdown_html("rpt_facilities", get_rpt_facilities(request.user), rpt_facilities),

                              }, context_instance=RequestContext(request)
                              )

def lab_submissions(request):
    today = date.today()
    startdate1 = read_date_or_default(request, 'start_date', today - timedelta(days=1))
    enddate1 = read_date_or_default(request, 'end_date', today)
    
    start_date = min(startdate1, enddate1, date.today())
    end_date = min(max(enddate1, startdate1, MWANA_ZAMBIA_START_DATE), date.today())

    start_date = end_date - timedelta(days=30)

    rpt_provinces = read_request(request, "rpt_provinces")
    rpt_districts = read_request(request, "rpt_districts")
    rpt_facilities = read_request(request, "rpt_facilities")


    service = GraphServive()
    report_data = []
    
    for k, v in service.get_lab_submissions(start_date, end_date, rpt_provinces\
                                            , rpt_districts,
                                            rpt_facilities).items():
        rpt_object = Expando()
        rpt_object.key = k.title()
        rpt_object.value = v
        report_data.append(rpt_object)

    return render_to_response('graphs/lab_submissions.html',
                              {
                              "x_axis":[(end_date - timedelta(days=i)).strftime('%d %b') for i in range(30, 0, -1)],
                              "title": "'Laboratory DBS Submissions to Mwana'",
                              "sub_title": "'%s  to %s'" % (start_date.strftime("%d %b %Y"), end_date.strftime("%d %b %Y")),
                              "label_y_axis": "'DBS samples'",
                              "report_data": report_data,
                              }, context_instance=RequestContext(request)
                              )