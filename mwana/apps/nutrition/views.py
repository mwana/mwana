#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from datetime import *
import os
import sys
import string
import csv

from django.http import HttpResponse
from django.db.models import Q

from django.template import RequestContext
from django.shortcuts import render_to_response
from django.views.generic.list import ListView
from django.core.paginator import Paginator, EmptyPage, InvalidPage

from .models import *
from .graphs import NutritionGraphs


DISTRICTS = ["Dedza", "Dowa", "Kasungu", "Lilongwe", "Mchinji", "Nkhotakota",
             "Ntcheu", "Ntchisi", "Salima", "Chitipa", "Karonga", "Likoma",
             "Mzimba", "Nkhata Bay", "Rumphi", "Balaka", "Blantyre", "Chikwawa",
             "Chiradzulu", "Machinga", "Mangochi", "Mulanje", "Mwanza", "Nsanje",
             "Thyolo", "Phalombe", "Zomba", "Neno"]

OEDEMA_VALUES = {1: "Yes", 0: "No", }

stat_options = {"All": "All", "Cancelled": "C", "Good": "G",
                    "Baseline": "B", "Suspect": "S"}

action_options = {"R-NRU": "NR", "C-OFP": "OF", "C-R": "RG", "R-SFP": "SF",
                     "X": "XX", "All": "All"}


def index(req):
    template_name = "nutrition/index.html"
    surveyentries = SurveyEntry.objects.order_by('-survey_date')
    assessments = ass_dicts_for_display()
    # sort by date, descending
    assessments.sort(lambda x, y: cmp(y['date'], x['date']))
    context = {'assessments': assessments, 'entries': surveyentries}
    return render_to_response(template_name, context,
                              context_instance=RequestContext(req))


def graphs(request):
    template_name = "nutrition/graphs.html"
    template_name_no_data = "nutrition/graphs_no_data.html"
    location, startdate, enddate = get_report_criteria(request)
    selected_location = str(location)
    gender_opts = {'Both': "Both", 'Male': "M", 'Female': "F"}
    startage = request.GET.get('startage', 0)
    endage = request.GET.get('endage', 60)
    selected_gender = request.GET.get('gender', "Both")
    asses = Assessment.objects.filter(Q(date__gte=startdate), Q(date__lte=enddate),
    Q(patient__age_in_months__gte=startage), Q(patient__age_in_months__lte=endage))
    if selected_gender != "Both":
        asses = asses.filter(patient__gender=selected_gender)
    if selected_location != "All Districts":
        r = NutritionGraphs(asses, selected_location)
        data = r.get_facilities_data()
    else:
        r = NutritionGraphs(asses)
        data = r.get_districts_data()
    if data:
        context = {'districts': sorted(DISTRICTS), 'gender_opts': gender_opts,
            'selected_gender': selected_gender,
            'enddate': enddate, 'selected_location': selected_location,
            'startdate': startdate, 'selected_percent': request.GET.get('percent', "checked"),
            'startage': startage, 'endage': endage,
            'weight_table': data['weight_table'], 'stunt_table': data['stunt_table'],
            'wasting_table': data['wasting_table'], 'weight_data': data['weight_data'],
            'stunt_data': data['stunt_data'], 'wasting_data': data['wasting_data'],
            'locations': data['locations'], 'weight_data_percent': data['weight_data_percent'],
            'stunt_data_percent': data['stunt_data_percent'],
            'wasting_data_percent': data['wasting_data_percent'],
            'chart_height': max((len(data['locations']) * 100), 700)}
        return render_to_response(template_name, context,
                              context_instance=RequestContext(request))
    else:
        context = {'districts': sorted(DISTRICTS), 'gender_opts': gender_opts,
            'selected_gender': selected_gender,
            'enddate': enddate, 'selected_location': selected_location,
            'startdate': startdate, 'selected_percent': request.GET.get('percent', "checked"),
            'startage': startage, 'endage': endage}
        return render_to_response(template_name_no_data, context,
                              context_instance=RequestContext(request))


def reports(request):
    template_name = "nutrition/reports.html"
    location, startdate, enddate = get_report_criteria(request)
    assessments = ass_dicts_for_display(location, startdate, enddate)
    selected_location = str(location)
    limited_assessments = assessments[:501]
    table = AssessmentTable(limited_assessments)
    table.paginate(page=request.GET.get('page', 1))
    context = {'table': table, 'selected_location': selected_location,
               'startdate': startdate, 'enddate': enddate, 'locations': sorted(DISTRICTS)}
    return render_to_response(template_name, context,
                              context_instance=RequestContext(request))


def assessments(request):
    location, startdate, enddate = get_report_criteria(request)
    selected_location = str(location)
    locations = sorted(DISTRICTS)
    status = request.GET.get('status', 'All')
    selected_status = str(status)
    action_taken = request.GET.get('action_taken', 'All')
    selected_action = str(action_taken)
    ass_list = Assessment.objects.filter(Q(date__gte=startdate),
                                      Q(date__lte=enddate)).order_by('-date')

    if location != "All Districts":
        filter_loc = Q(healthworker__location__parent__parent__name=location)
        ass_list = ass_list.filter(filter_loc)
    if status != "All":
        ass_list = ass_list.filter(status=stat_options[status])
    if action_taken != "All":
        ass_list = ass_list.filter(action_taken=action_options[action_taken])

    paginator = Paginator(ass_list, 50)
    try:
        page = int(request.GET.get('page', '1'))
    except:
        page = 1

    try:
        ass_list = paginator.page(page)
    except(EmptyPage, InvalidPage):
        ass_list = paginator.page(paginator.num_pages)

    context = {'selected_location': selected_location,
               'startdate': startdate, 'enddate': enddate,
               'locations': locations, 'status': status,
               'selected_status': selected_status,
               'stat_options': sorted(stat_options.keys()),
               'action_options': sorted(action_options.keys()),
               'selected_action': selected_action,
               'ass_list': ass_list}

    return render_to_response("nutrition/assessment_list.html", context,
                                                             context_instance=RequestContext(request))


def instance_to_dict(instance):
    dict = {}
    for field in instance._meta.fields:

        # skip foreign keys. for now... TODO
        if (hasattr(field, "rel")) and (field.rel is not None):  # and (depth < max_depth):
                # columns.extend(build_row(field.rel.to, cell, depth+1))
                continue
        value = getattr(instance, field.name)

        # append to dict if its not None, this way the django template
        # will leave a blank space rather than listing 'None'
        if value is not None:
            dict.update({field.name: value})
        if value is None:
            dict.update({field.name: ""})
    return dict


def ass_dicts_for_display(location, startdate, enddate):
    dicts_for_display = []
    asses = Assessment.objects.filter(Q(date__gte=startdate),
                                      Q(date__lte=enddate)).order_by('-date').\
                                      select_related()
    if location != "All Districts":
        asses = asses.filter(healthworker__location__parent__parent__name=location)
    for ass in asses:
        ass_dict = {}
        # add desired fields from related models (we want to display the
        # IDs, ect from foreign fields rather than just the unicode() names
        # or all of the fields from related models)
        # TODO is there a better way to do this? adding fields to the queryset???
        ass_dict.update({'interviewer_name': ass.healthworker.name})
        ass_dict.update({'location': ass.healthworker.clinic})
        ass_dict.update({'child_id': ass.patient.code})
        ass_dict.update({'sex': ass.patient.gender})
        ass_dict.update({'date_of_birth': ass.patient.date_of_birth})
        ass_dict.update({'age_in_months': ass.patient.age_in_months})
        ass_dict.update({'human_status': ass.get_status_display()})
        ass_dict.update({'underweight': ass.get_underweight_display()})
        ass_dict.update({'stunting': ass.get_stunting_display()})
        ass_dict.update({'wasting': ass.get_wasting_display()})
        ass_dict.update(**instance_to_dict(ass))
        dicts_for_display.append(ass_dict)
    return dicts_for_display


def get_human_oedema(value):
    if value == 1:
        return "Yes"
    if value == 0:
        return "No"


# TODO DRY
def ass_dicts_for_export(location, startdate, enddate, gender, startage, endage, status, action_taken):
    dicts_for_export = []
    asses = Assessment.objects.all().order_by('-date').select_related()
    if location != "All Districts":
        asses = asses.filter(healthworker__location__parent__parent__name=location)
    if gender != "Both":
        asses = asses.filter(patient__gender=gender)
    if status != "All":
            asses = asses.filter(status=stat_options[status])
    if action_taken != "All":
        asses = asses.filter(action_taken=action_options[action_taken])
    asses = asses.filter(Q(date__gte=startdate), Q(date__lte=enddate),
    Q(patient__age_in_months__gte=startage), Q(patient__age_in_months__lte=endage))
    for ass in asses:
        ass_dict = {}
        # add desired fields from related models (we want to display the
        # IDs, ect from foreign fields rather than just the unicode() names
        # or all of the fields from related models)
        # TODO is there a better way to do this? adding fields to the
        # queryset???
        ass_dict.update({'interviewer_name': ass.healthworker.name})
        ass_dict.update({'location': ass.healthworker.clinic})
        ass_dict.update({'district': ass.healthworker.clinic.parent.name})
        ass_dict.update({'child_id': ass.patient.code})
        ass_dict.update({'sex': ass.patient.gender})
        ass_dict.update({'date_of_birth': ass.patient.date_of_birth})
        ass_dict.update({'age_in_months': ass.patient.age_in_months})
        ass_dict.update({'human_status': ass.get_status_display()})
        ass_dict.update({'underweight_status': ass.get_underweight_display()})
        ass_dict.update({'stunting_status': ass.get_stunting_display()})
        ass_dict.update({'wasting_status': ass.get_wasting_display()})
        ass_dict.update(**instance_to_dict(ass))
        ass_dict.update({'oedema': get_human_oedema(ass.oedema)})
        ass_dict.update({'action_taken': ass.action_taken})
        dicts_for_export.append(ass_dict)
    return dicts_for_export


def export(headers, keys, objects, file_name):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=%s' % file_name

    writer = csv.writer(response)
    # column labels
    writer.writerow(headers)
    for obj in objects:
        row = []
        sep = "."
        for key in keys:
            if isinstance(obj, dict) and key in obj:
                row.append(obj[key])
            elif hasattr(obj, key):
                row.append(getattr(obj, key))
            elif sep in key:
                # assuming healthworker, clean this up later.
                list = key.split(sep)
                if hasattr(obj.healthworker, list[1]):
                    row.append(getattr(obj.healthworker, list[1]))
            else:
                row.append("None")
        writer.writerow([unicode(s).encode("utf-8") for s in row])

    return response


def csv_assessments(req):
    headers = ['Date Submitted', 'Facility', 'District', 'Interviewer Name',
               'Child ID', 'Sex', 'Date of Birth', 'Age in months', 'Height',
               'Weight', 'Oedema', 'MUAC', 'Weight for height Z', 'Wasting',
               'Weight for age Z', 'Underweight', 'Height for age Z',
               'Stunting', 'Data Quality', 'Action Taken',]
    keys = ['date', 'location', 'district', 'interviewer_name', 'child_id',
            'sex', 'date_of_birth', 'age_in_months',
            'height', 'weight', 'oedema', 'muac', 'weight4height',
            'wasting_status', 'weight4age', 'underweight_status', 'height4age',
            'stunting_status', 'human_status', 'action_taken']

    location, startdate, enddate = get_report_criteria(req)
    gender = req.GET.get('gender', 'Both')
    startage = req.GET.get('startage', 0)
    endage = req.GET.get('endage', 60)
    status = req.GET.get('status', 'All')
    action_taken = req.GET.get('action_taken', 'All')
    assessments = ass_dicts_for_export(location, startdate, enddate, gender, startage, endage, status, action_taken)
    # sort by date, descending
    #assessments.sort(lambda x, y: cmp(y['date'], x['date']))
    return export(headers, keys, assessments, 'assessments.csv')


def csv_entries(req):
    headers = ['Date Submitted', 'Facility', 'Interviewer Name', 'Child ID',
               'Sex', 'Date of Birth', 'Age in months', 'Height',
               'Weight', 'Oedema', 'MUAC']
    keys = ['survey_date', 'healthworker.clinic', 'healthworker.name', 'child_id',
            'gender', 'date_of_birth', 'age_in_months',
            'height', 'weight', 'oedema', 'muac']
    return export(headers, keys, SurveyEntry.objects.all(), 'entries.csv')


def survey_locations():
    districts = []

    def uniq(seq):
        seen = set()
        seen_add = seen.add
        return [x for x in seq if x not in seen and not seen_add(x)]

    for assesment in Assessment.objects.all().select_related():
        districts.append(str(assesment.healthworker.clinic.parent))

    return uniq(districts)


def get_report_criteria(request):
    location = request.GET.get('location', 'All Districts')
    default_end_date = datetime.today().date()
    default_start_date = default_end_date - timedelta(days=30)
    startdate = request.GET.get('startdate', default_start_date.strftime("%Y-%m-%d"))
    enddate = request.GET.get('enddate', default_end_date.strftime("%Y-%m-%d"))

    return location, startdate, enddate
