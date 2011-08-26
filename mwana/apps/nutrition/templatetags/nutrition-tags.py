#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
from datetime import datetime, timedelta

from django import template
register = template.Library()
from django.db.models import Avg

from rapidsms.webui.utils import * 

from nutrition.models import *

@register.inclusion_tag("nutrition/partials/stats.html")
@dashboard("top_right", "nutrition/partials/stats.html", "nutrition.can_view")
def nutrition_stats():
    return { "stats": [
        {
            "caption": "Teams",
            "value":   HealthWorker.objects.count()
        },
        {
            "caption": "Children",
            "value":   Patient.objects.count()
        },
        {
            "caption": "Total Survey Entries",
            "value":   SurveyEntry.objects.count()
        },
        {
            "caption": "Valid Surveys",
            "value":   Assessment.objects.count()
        },
        {
            "caption": "Suspect Surveys",
            "value":   Assessment.objects.filter(status='S').count()
        }
    ]}

@register.inclusion_tag("nutrition/partials/progress.html")
@dashboard("top_middle", "nutrition/partials/progress.html", "nutrition.can_view")
def nutrition_progress():
    def unique_list(seq):
        set = {}
        map(set.__setitem__, seq, [])
        return set.keys()
    try:
        survey = Survey.objects.get(begin_date__lte=datetime.datetime.now().date(),\
            end_date__gte=datetime.datetime.now().date())

    except ObjectDoesNotExist, MultipleObjectsReturned:
        survey = Survey.objects.filter(end_date__lte=datetime.datetime.now()\
                    .date()).order_by('begin_date')[0]
    start = survey.begin_date
    end = survey.end_date
    days = []
    for d in range(0, (end - start).days):
        date = start + datetime.timedelta(d)
        
        ass_args = {
            "date__year":  date.year,
            "date__month": date.month,
            "date__day":   date.day
        }
        
        data = {
            "number": d+1,
            "date": date,
            "in_future": date > datetime.datetime.now().date()
        }
        
        if not data["in_future"]:
            healthworkers_today = SurveyEntry.objects.filter(survey_date__year=date.\
                    year, survey_date__month=date.month, survey_date__day=\
                    date.day).values_list('healthworker_id', flat=True)
            unique_healthworkers_today = unique_list(healthworkers_today)
            data.update({
                "children": Patient.objects.filter(created_at__year=date.year,\
                    created_at__month=date.month, created_at__day=date.day\
                    ).count(),
                "healthworkers": len(unique_healthworkers_today),
                "surveys": SurveyEntry.objects.filter(survey_date__year=date.\
                    year, survey_date__month=date.month, survey_date__day=\
                    date.day).count(),
                "valids": Assessment.objects.filter(**ass_args).count(),
                "goods": Assessment.objects.filter(**ass_args).filter(\
                    status='G').count(),
                "suspects": Assessment.objects.filter(**ass_args).filter(\
                    status='S').count()
            })
        
            data.update({
                "valid_perc":    int((float(data["valids"])    / float(data["surveys"]))    * 100.0) if (data["valids"]    > 0) else 0,
                "good_perc":    int((float(data["goods"])    / float(data["surveys"]))    * 100.0) if (data["goods"]    > 0) else 0,
                "suspect_perc":    int((float(data["suspects"])    / float(data["surveys"]))    * 100.0) if (data["suspects"]    > 0) else 0,
            })
        days.append(data)
    active_healthworkers = unique_list(SurveyEntry.objects.all().values_list(\
        'healthworker_id', flat=True))
    return {
        "days" : days,
        "total_children" : Patient.objects.all().count(),
        "active_healthworkers" : len(active_healthworkers),
        "total_surveys": SurveyEntry.objects.all().count(),
        "total_valids": Assessment.objects.all().count(),
        "total_goods": Assessment.objects.all().filter(status='G').count(),
        "total_suspects": Assessment.objects.all().filter(status='S').count()
    }

@register.inclusion_tag("nutrition/partials/healthworkers.html")
@dashboard("bottom_left", "nutrition/partials/healthworkers.html", "nutrition.can_view")
def nutrition_healthworkers():
    healthworkers_infos = []
    hws = HealthWorker.objects.filter(status="A")
    for hw in hws:
        info = {
            "first_name" : hw.first_name,
            "last_name" : hw.last_name,
            "interviewer_id" : hw.interviewer_id,
            "last_seen" : hw.last_seen(),
            "num_message_count" : hw.num_messages_sent(),
            "num_message_month" : hw.num_messages_sent("month"),
            "num_message_week" : hw.num_messages_sent("week"),
            "num_message_today" : hw.num_messages_sent("today"),
            "surveys_today" : Assessment.objects.filter(\
                healthworker=hw.pk, date__gte=datetime.datetime.now().date())\
                .count(),
            "goods" : Assessment.objects.filter(status="G",\
                healthworker=hw.pk).count(),
            "suspects" : Assessment.objects.filter(status="S",\
                healthworker=hw.pk).count()
        }
        healthworkers_infos.append(info)

    healthworkers_infos.sort(lambda x, y: cmp(y['surveys_today'], x['surveys_today']))
    return { "healthworkers" : healthworkers_infos }
