# vim: ai ts=4 sts=4 et sw=4
from datetime import datetime
from operator import itemgetter

from django.db.models import Count
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext

from mwana.apps.locations.models import Location

from .forms import NationalStatisticsFilterForm
from .models import (PregnantMother, BirthRegistration, DeathRegistration,
                        FacilityVisit)
from .tables import PregnantMotherTable, HistoryTable, StatisticsTable
from .utils import export_as_csv, filter_by_dates


def mothers(request):
    mothers_table = PregnantMotherTable(PregnantMother.objects.all(),
                                        request=request)
    return render_to_response(
        "smgl/mothers.html",
        {"mothers_table": mothers_table
        },
        context_instance=RequestContext(request))


def mother_history(request, id):
    mother = get_object_or_404(PregnantMother, id=id)
    # TODO: aggregate the messages for a mother into a
    messages = mother.get_all_messages()
    return render_to_response(
        "smgl/mother_history.html",
        {"mother": mother,
          "history_table": HistoryTable(messages,
                                        request=request)
        },
        context_instance=RequestContext(request))


def statistics(request):
    records = []
    province = district = start_date = end_date = None

    visits = FacilityVisit.objects.all()

    if request.GET:
        form = NationalStatisticsFilterForm(request.GET)
    else:
        form = NationalStatisticsFilterForm()

    if form.is_valid():
        province = form.cleaned_data.get('province')
        district = form.cleaned_data.get('district')
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
    # determine what district(s) to include in the report
    if province:
        districts = Location.objects.filter(parent=province)
    elif district:
        districts = [district]
    else:
        districts = Location.objects.filter(type__singular='district')

    for district in districts:
        r = {'district': district}
        births = BirthRegistration.objects.filter(district=district)
        # utilize start/end date if supplied
        births = filter_by_dates(births, 'date',
                                 start=start_date, end=end_date)
        r['births_com'] = births.filter(place='h').count()
        r['births_fac'] = births.filter(place='f').count()
        r['births_total'] = r['births_com'] + r['births_fac']

        deaths = DeathRegistration.objects.filter(district=district)
        deaths = filter_by_dates(deaths, 'date',
                                 start=start_date, end=end_date)

        r['infant_deaths_com'] = deaths.filter(place='h',
                                               person='inf').count()
        r['infant_deaths_fac'] = deaths.filter(place='f',
                                               person='inf').count()
        r['infant_deaths_total'] = r['infant_deaths_com'] \
                                    + r['infant_deaths_fac']

        r['mother_deaths_com'] = deaths.filter(place='h',
                                               person='ma').count()
        r['mother_deaths_fac'] = deaths.filter(place='f',
                                               person='ma').count()
        r['mother_deaths_total'] = r['mother_deaths_com'] \
                                    + r['mother_deaths_fac']

        # Aggregate ANC visits by Mother and # of visits
        district_visits = visits.filter(district=district)
        district_visits = filter_by_dates(district_visits, 'visit_date',
                                  start=start_date, end=end_date)

        mother_ids = district_visits.distinct('mother') \
                        .values_list('mother', flat=True)
        num_visits = {}
        mothers = PregnantMother.objects.filter(id__in=mother_ids)

        mother_visits = mothers.annotate(Count('facility_visits')).values_list('facility_visits__count', flat=True)

        r['anc1'] = r['anc2'] = r['anc3'] = r['anc4'] = None

        for num in mother_visits:
            if num in num_visits:
                num_visits[num] += 1
            else:
                num_visits[num] = 1
        for i in range(1, 5):
            key = 'anc{0}'.format(i)
            if i in num_visits:
                r[key] = num_visits[i]

        # TO DO when POS keyword handler is in place
        r['pos1'] = None
        r['pos2'] = None
        r['pos3'] = None
        records.append(r)

    # handle sorting, since djtables won't sort on non-Model based tables.
    if request.GET.get('order_by'):
        reverse = False
        attr = request.GET.get('order_by')
        if attr.startswith('-'):
            reverse = True
        attr = attr.strip('-')
        try:
            records = sorted(records, key=itemgetter(attr))
        except KeyError:
            pass
        if reverse:
            records.reverse()

    # render as CSV if export
    if form.data.get('export'):
        # The keys must be ordered for the exporter
        keys = ['district', 'births_com', 'births_fac', 'births_total',
                'infant_deaths_com', 'infant_deaths_fac',
                'infant_deaths_total', 'mother_deaths_com',
                'mother_deaths_fac', 'mother_deaths_total', 'anc1', 'anc2',
                'anc3', 'anc4', 'pos1', 'pos2', 'pos3']
        filename = 'national_statistics'
        date_range = ''
        if start_date:
            date_range = '_from{0}'.format(start_date)
        if start_date:
            date_range = '{0}_to{1}'.format(date_range, end_date)
        filename = '{0}{1}'.format(filename, date_range)
        return export_as_csv(records, keys, filename)

    statistics_table = StatisticsTable(records,
                                       request=request)
    return render_to_response(
        "smgl/statistics.html",
        {"statistics_table": statistics_table,
         "form": form
        },
        context_instance=RequestContext(request))
