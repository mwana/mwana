# vim: ai ts=4 sts=4 et sw=4

from django import template
from mwana.apps.labresults.models import Result
from mwana.apps.nutrition.models import Assessment
from mwana.apps.reminders.models import PatientEvent

register = template.Library()


@register.inclusion_tag('labresults/templatetags/labresults_map.html', takes_context=True)
def render_location(context):
    return {"location": context['location'], "startdate": context['startdate']}


@register.inclusion_tag('labresults/templatetags/dbs_results.html', takes_context=True)
def render_dbs_results(context):
    results = Result.objects.filter(clinic=context['location'],
                                    result_sent_date__gte=context['startdate']).count()
    return {'dbs_results': results}


@register.inclusion_tag('labresults/templatetags/remindmis.html', takes_context=True)
def render_remindmis(context):
    remindmis = PatientEvent.objects.filter(date_logged__gte=context['startdate'], patient__location__parent__name=context['location']).order_by('-date')
    mothers = remindmis.filter(event__name="Care program").count()
    children = remindmis.filter(event__name="Birth").count()
    return {'mothers': mothers, 'children': children}


@register.inclusion_tag('labresults/templatetags/anthrowatch.html', takes_context=True)
def render_anthrowatch(context):
    assessments = Assessment.objects.filter(date__gte=context['startdate'], healthworker__location__parent__name=context['location']).count()
    return {'assessments': assessments}
