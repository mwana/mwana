#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from datetime import *
import os,sys,string
import csv

from django.http import HttpResponse
from django.db.models import Q

from django.template import RequestContext
from django.shortcuts import redirect, get_object_or_404, render_to_response

from .models import *
from .table import AssessmentTable

def index(req):
    template_name="nutrition/index.html"
    surveyentries = SurveyEntry.objects.order_by('-survey_date')
    assessments = ass_dicts_for_display()
    # sort by date, descending
    assessments.sort(lambda x, y: cmp(y['date'], x['date']))
    context = {'assessments': assessments, 'entries': surveyentries}
    return render_to_response(template_name, context,
                              context_instance=RequestContext(req))

    
def reports(request):
    template_name="nutrition/reports.html"
    location, startdate, enddate = get_report_criteria(request)
    assessments = ass_dicts_for_display(location, startdate, enddate)
    selected_location = str(location)
    locations = survey_locations()
    locations.append("All Districts")
    #locations = sorted(list(set(locations)))
    # sort by date, newest at top
    assessments.sort(lambda x, y: cmp(y['date'], x['date']))
    table = AssessmentTable(assessments)
    table.paginate(page=request.GET.get('page', 1))
    context = {'table': table, 'selected_location': selected_location, 
    'startdate': startdate, 'enddate': enddate, 'locations': locations}
    return render_to_response(template_name, context,
                              context_instance=RequestContext(request))

    
def instance_to_dict(instance):
    dict = {}
    for field in instance._meta.fields:

        # skip foreign keys. for now... TODO
        if (hasattr(field, "rel")) and (field.rel is not None):# and (depth < max_depth):
                #columns.extend(build_row(field.rel.to, cell, depth+1))
                continue
        value = getattr(instance, field.name)

        # append to dict if its not None, this way the django template
        # will leave a blank space rather than listing 'None'
        if value is not None:
            dict.update({ field.name : value })
    return dict


def ass_dicts_for_display(location, startdate, enddate):
    dicts_for_display = []
    asses = Assessment.objects.all().select_related()
    if location != "All Facilities":
        asses = asses.filter(healthworker__location__parent__parent__name=location)
    asses = asses.filter(Q(date__gte=startdate), Q(date__lte=enddate))
    for ass in asses:
        ass_dict = {}
        # add desired fields from related models (we want to display the
        # IDs, ect from foreign fields rather than just the unicode() names
        # or all of the fields from related models)
        # TODO is there a better way to do this? adding fields to the queryset???
        ass_dict.update({'interviewer_name'   : ass.healthworker.name})
        ass_dict.update({'location'          : ass.healthworker.clinic})
        ass_dict.update({'child_id'         : ass.patient.code})
        #ass_dict.update({'household_id'     : ass.patient.household_id})
        #ass_dict.update({'cluster_id'       : ass.patient.cluster_id})
        ass_dict.update({'sex'              : ass.patient.gender})
        ass_dict.update({'date_of_birth'    : ass.patient.date_of_birth})
        ass_dict.update({'age_in_months'    : ass.patient.age_in_months})
        ass_dict.update({'human_status'     : ass.get_status_display()})
        ass_dict.update({'w4astatus'     : ass.get_w4astatus_display()})
        ass_dict.update({'h4astatus'     : ass.get_h4astatus_display()})
        ass_dict.update({'w4hstatus'     : ass.get_w4hstatus_display()})
        ass_dict.update({'muac_status'     : ass.get_muac_status_display()})
        ass_dict.update(**instance_to_dict(ass))
        dicts_for_display.append(ass_dict)
    return dicts_for_display


# TODO DRY
def ass_dicts_for_export(location, startdate, enddate):
    dicts_for_export = []
    asses = Assessment.objects.all().select_related()
    if location != "All Facilities":
        asses = asses.filter(healthworker__location__parent__name=location)
    asses = asses.filter(Q(date__gte=startdate), Q(date__lte=enddate))
    for ass in asses:
        ass_dict = {}
        # add desired fields from related models (we want to display the
        # IDs, ect from foreign fields rather than just the unicode() names
        # or all of the fields from related models)
        # TODO is there a better way to do this? adding fields to the
        # queryset???
        ass_dict.update({'interviewer_name'   : ass.healthworker.name})
        ass_dict.update({'location'          : ass.healthworker.clinic})
        ass_dict.update({'child_id'         : ass.patient.code})
        #ass_dict.update({'household_id'     : ass.patient.household_id})
        #ass_dict.update({'cluster_id'       : ass.patient.cluster_id})
        ass_dict.update({'sex'              : ass.patient.gender})
        ass_dict.update({'date_of_birth'    : ass.patient.date_of_birth})
        ass_dict.update({'age_in_months'    : ass.patient.age_in_months})
        ass_dict.update({'human_status'     : ass.get_status_display()})
        ass_dict.update({'w4a_status'     : ass.get_w4astatus_display()})
        ass_dict.update({'h4a_status'     : ass.get_h4astatus_display()})
        ass_dict.update({'w4h_status'     : ass.get_w4hstatus_display()})
        ass_dict.update({'mstatus'     : ass.get_muac_status_display()})
        ass_dict.update(**instance_to_dict(ass))
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
        writer.writerow(row)

    return response


def csv_assessments(req):
    headers = ['Date Submitted', 'Facility', 'Interviewer Name', 'Child ID',    
        'Sex', 'Date of Birth', 'Age in months', 'Height',
        'Weight', 'Oedema', 'MUAC', 'MUAC Status','Height for age',
        'Height for Age Status', 'Weight for age', 'Weight for Age Status',
        'Weight for height', 'Weight for Height Status', 'Data Quality']
    keys = ['date', 'location', 'interviewer_name', 'child_id',
            'sex', 'date_of_birth', 'age_in_months',
            'height', 'weight', 'oedema', 'muac', 'mstatus',
            'height4age', 'h4a_status', 'weight4age', 'w4a_status',
            'weight4height', 'w4h_status', 'human_status']
    
    location, startdate, enddate = get_report_criteria(req)
    assessments = ass_dicts_for_export(location, startdate, enddate)
    # sort by date, descending
    assessments.sort(lambda x, y: cmp(y['date'], x['date']))
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
        return [ x for x in seq if x not in seen and not seen_add(x)]        

    for assesment in Assessment.objects.all().select_related():
        districts.append(str(assesment.healthworker.clinic.parent))
        
    return uniq(districts)

def get_report_criteria(request):
    location = request.GET.get('location', 'All Facilities')
    default_end_date = datetime.today().date()
    default_start_date = default_end_date - timedelta(days=30)
    startdate = request.GET.get('startdate', default_start_date)
    enddate = request.GET.get('enddate', default_end_date)

    return location, startdate, enddate

