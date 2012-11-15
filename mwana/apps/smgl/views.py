# vim: ai ts=4 sts=4 et sw=4
import urllib

from datetime import date

from operator import itemgetter

from django.db.models import Count, Q
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext

from mwana.apps.contactsplus.models import ContactType

from mwana.apps.locations.models import Location

from .forms import StatisticsFilterForm
from .models import (PregnantMother, BirthRegistration, DeathRegistration,
                        FacilityVisit, Referral, ToldReminder,
                        ReminderNotification)
from .tables import (PregnantMotherTable, HistoryTable, StatisticsTable,
                        StatisticsLinkTable, ReminderStatsTable)
from .utils import (export_as_csv, filter_by_dates, get_current_district,
    get_location_tree_nodes, percentage)


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


def statistics(request, id=None):
    records = []
    facility_parent = None
    province = district = facility = start_date = end_date = None

    visits = FacilityVisit.objects.all()
    records_for = Location.objects.filter(type__singular='district')

    if id:
        facility_parent = get_object_or_404(Location, id=id)
        # Prepopulate the district
        if not request.GET:
            update = {u'district_0': facility_parent.name,
                      u'district_1': facility_parent.id}
            request.GET = request.GET.copy()
            request.GET.update(update)

    if request.GET:
        form = StatisticsFilterForm(request.GET)
        if form.is_valid():
            province = form.cleaned_data.get('province')
            district = form.cleaned_data.get('district')
            facility = form.cleaned_data.get('facility')
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')
        # determine what location(s) to include in the report
        if id:
            # get district facilities
            records_for = get_location_tree_nodes(facility_parent)
            if district:
                records_for = get_location_tree_nodes(district)
                if facility_parent != district:
                    redirect_url = reverse('district-stats',
                                            args=[district.id])
                    params = urllib.urlencode(request.GET)
                    full_redirect_url = '%s?%s' % (redirect_url, params)
                    return HttpResponseRedirect(full_redirect_url)
            if facility:
                records_for = [facility]
        else:
            if province:
                records_for = Location.objects.filter(parent=province)
            if district:
                records_for = [district]
    else:
        form = StatisticsFilterForm()

    for place in records_for:
        reg_filter = {'district': place}
        visit_filter = {'district': place}
        if id:
            reg_filter = {'facility': place}
            visit_filter = {'location': place}
        r = {'location': place.name}
        r['location_id'] = place.id
        births = BirthRegistration.objects.filter(**reg_filter)
        # utilize start/end date if supplied
        births = filter_by_dates(births, 'date',
                                 start=start_date, end=end_date)
        r['births_com'] = births.filter(place='h').count()
        r['births_fac'] = births.filter(place='f').count()
        r['births_total'] = r['births_com'] + r['births_fac']

        deaths = DeathRegistration.objects.filter(**reg_filter)
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
        place_visits = visits.filter(**visit_filter)
        place_visits = filter_by_dates(place_visits, 'visit_date',
                                  start=start_date, end=end_date)

        mother_ids = place_visits.distinct('mother') \
                            .values_list('mother', flat=True)
        num_visits = {}
        mothers = PregnantMother.objects.filter(id__in=mother_ids)

        mother_visits = mothers.annotate(Count('facility_visits')) \
                            .values_list('facility_visits__count', flat=True)

        r['anc1'] = r['anc2'] = r['anc3'] = r['anc4'] = 0

        for num in mother_visits:
            if num in num_visits:
                num_visits[num] += 1
            else:
                num_visits[num] = 1
        for i in range(1, 5):
            key = 'anc{0}'.format(i)
            if i in num_visits:
                r[key] = num_visits[i]

        # Get PregnantMother count for each place
        if not id:
            locations = Location.objects.all()
            district_facilities = [x for x in locations \
                                if get_current_district(x) == place]
            pregnancies = PregnantMother.objects \
                            .filter(location__in=district_facilities)
        else:
            pregnancies = PregnantMother.objects.filter(location=place)

        pregnancies = filter_by_dates(pregnancies, 'created_date',
                                 start=start_date, end=end_date)

        r['pregnancies'] = pregnancies.count()

        # TO DO when POS keyword handler is in place
        r['pos1'] = r['pos2'] = r['pos3'] = 0
        records.append(r)

    # handle sorting, since djtables won't sort on non-Model based tables.
    records = sorted(records, key=itemgetter('location'))
    if request.GET.get('order_by'):
        sort = False
        attr = request.GET.get('order_by')
        if attr.startswith('-'):
            sort = True
        attr = attr.strip('-')
        try:
            records = sorted(records, key=itemgetter(attr))
        except KeyError:
            pass
        if sort:
            records.reverse()

    # render as CSV if export
    if form.data.get('export'):
        # The keys must be ordered for the exporter
        keys = ['location', 'births_com', 'births_fac', 'births_total',
                'infant_deaths_com', 'infant_deaths_fac',
                'infant_deaths_total', 'mother_deaths_com',
                'mother_deaths_fac', 'mother_deaths_total', 'anc1', 'anc2',
                'anc3', 'anc4', 'pos1', 'pos2', 'pos3']
        filename = 'national_statistics' if not id else 'district_statistics'
        date_range = ''
        if start_date:
            date_range = '_from{0}'.format(start_date)
        if start_date:
            date_range = '{0}_to{1}'.format(date_range, end_date)
        filename = '{0}{1}'.format(filename, date_range)
        return export_as_csv(records, keys, filename)

    statistics_table = StatisticsLinkTable(records,
                                           request=request)
    # disable the link column if on district stats view
    if id:
        statistics_table = StatisticsTable(records,
                                           request=request)
    return render_to_response(
        "smgl/statistics.html",
        {"statistics_table": statistics_table,
         "district": facility_parent,
         "form": form
        },
        context_instance=RequestContext(request))


def reminder_stats(request):
    records = []
    province = district = facility = start_date = end_date = None
    record_types = ['edd', 'nvd', 'ref']
    if request.GET:
        form = StatisticsFilterForm(request.GET)
        if form.is_valid():
            province = form.cleaned_data.get('province')
            district = form.cleaned_data.get('district')
            facility = form.cleaned_data.get('facility')
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')
    else:
        form = StatisticsFilterForm()

    for key in record_types:
        mothers = PregnantMother.objects.all()
        # filter by location if needed...
        locations = Location.objects.all()
        if province:
            locations = get_location_tree_nodes(province)
        if district:
            locations = get_location_tree_nodes(district)
        if facility:
            locations = [facility]
        mothers = mothers.filter(location__in=locations)
        reminders = ReminderNotification.objects.filter(type__icontains=key,
                                                        mother__in=mothers)
        # utilize start/end date if supplied
        reminders = filter_by_dates(reminders, 'date',
                                 start=start_date, end=end_date)
        reminded_mothers = reminders.values_list('mother', flat=True)
        tolds = ToldReminder.objects.filter(type=key,
                                            mother__in=reminded_mothers
                                            )
        if key == 'edd':
            showed_up = BirthRegistration.objects.filter(
                                                mother__in=reminded_mothers
                                                )
        elif key == 'ref':
            showed_up = Referral.objects.filter(mother_showed=True,
                                                mother__in=reminded_mothers
                                                )
        else:
            showed_up = FacilityVisit.objects.filter(
                                                    mother__in=reminded_mothers
                                                    )
        records.append({
                'reminder_type': key,
                'reminders': reminders.count(),
                'told': tolds.count(),
                'showed_up': showed_up.count()
            })

    # render as CSV if export
    if form.data.get('export'):
        # The keys must be ordered for the exporter
        keys = ['reminder_type', 'reminders', 'told', 'showed_up']
        filename = 'reminder_statistics'
        date_range = ''
        if start_date:
            date_range = '_from{0}'.format(start_date)
        if start_date:
            date_range = '{0}_to{1}'.format(date_range, end_date)
        filename = '{0}{1}'.format(filename, date_range)
        return export_as_csv(records, keys, filename)

    reminder_stats_table = ReminderStatsTable(records,
                                           request=request)

    return render_to_response(
        "smgl/reminder_stats.html",
        {"reminder_stats_table": reminder_stats_table,
         "form": form
        },
        context_instance=RequestContext(request))


def report(request):
    province = district = locations = None
    start_date = date(date.today().year, 1, 1)
    end_date = date(date.today().year, 12, 31)

    if request.GET:
        form = StatisticsFilterForm(request.GET)
        if form.is_valid():
            province = form.cleaned_data.get('province')
            district = form.cleaned_data.get('district')
            form_start_date = form.cleaned_data.get('start_date')
            form_end_date = form.cleaned_data.get('end_date')
            if form_start_date:
                start_date = form_start_date
            if form_end_date:
                end_date = form_end_date
    else:
        form = StatisticsFilterForm()

    if province:
        # districts are direct children
        locations = province.location_set.all()
    if district:
        locations = [district]

    deaths = DeathRegistration.objects.filter(person='ma')
    deaths = filter_by_dates(deaths, 'date', start=start_date, end=end_date)
    if locations:
        deaths = DeathRegistration.objects.filter(district__in=locations)
    mortality_rate = percentage(deaths.count(), 100000)

    cbas = ContactType.objects.get(slug='cba').contacts.all()
    cbas = filter_by_dates(cbas, 'created_date',
                           start=start_date, end=end_date)
    clerks = ContactType.objects.get(slug='dc').contacts.all()
    clerks = filter_by_dates(clerks, 'created_date',
                             start=start_date, end=end_date)
    workers = ContactType.objects.get(slug='worker').contacts.all()
    workers = filter_by_dates(workers, 'created_date',
                              start=start_date, end=end_date)
    if locations:
        cbas = [x for x in cbas if x.get_current_district() in locations]
        clerks = [x for x in clerks if x.get_current_district() in locations]
        workers = [x for x in workers if x.get_current_district() in locations]

    # agregating ANC numbers
    visits = filter_by_dates(FacilityVisit.objects.all(), 'created_date',
                             start=start_date, end=end_date)
    if locations:
        visits = visits.filter(district__in=locations)

    mother_ids = visits.distinct('mother').values_list('mother', flat=True)
    mothers = PregnantMother.objects.filter(id__in=mother_ids)
    mother_visits = mothers.annotate(Count('facility_visits')) \
                            .values_list('facility_visits__count', flat=True)
    gte_four_ancs = sum(i >= 4 for i in mother_visits)

    # agregating referral information
    non_ems_refs = filter_by_dates(Referral.non_emergencies(), 'date',
                                   start=start_date, end=end_date)
    ems_refs = filter_by_dates(Referral.emergencies(), 'date',
                                   start=start_date, end=end_date)

    outcomes = Q(mother_outcome__isnull=False) | Q(baby_outcome__isnull=False)
    positive_outcomes = Q(mother_outcome='stb') | Q(baby_outcome='stb')
    non_ems_wro = non_ems_refs.filter(outcomes, responded=True).count()
    non_ems_wro = percentage(non_ems_wro, non_ems_refs.count())
    ems_wro = ems_refs.filter(outcomes, responded=True).count()
    ems_wro = percentage(ems_wro, ems_refs.count())
    positive_ems_wro = ems_refs.filter(positive_outcomes, responded=True).count()
    positive_ems_wro = percentage(positive_ems_wro, ems_refs.count())

    # computing birth and death percentages
    births = filter_by_dates(BirthRegistration.objects.all(), 'date',
                               start=start_date, end=end_date)
    if locations:
        births = births.filter(district__in=locations)

    f_births = percentage(births.filter(place='f').count(), births.count())
    c_births = percentage(births.filter(place='h').count(), births.count())

    deaths = filter_by_dates(DeathRegistration.objects.filter(person='inf'),
                              'date', start=start_date, end=end_date)
    if locations:
        deaths = deaths.filter(district__in=locations)

    f_deaths = percentage(deaths.filter(place='f').count(), deaths.count())
    c_deaths = percentage(deaths.filter(place='h').count(), deaths.count())

    #anc reminders
    reminders = filter_by_dates(ReminderNotification.objects.filter(type='nvd'),
                               'date', start=start_date, end=end_date)
    reminded_mothers = reminders.values_list('mother', flat=True)
    visits = visits.filter(mother__in=reminded_mothers)

    returned = percentage(visits.count(), reminded_mothers.count())

    return render_to_response(
        "smgl/report.html",
        {"form": form,
         "mortality_rate": mortality_rate,
         "cbas": cbas,
         "clerks": clerks,
         "workers": workers,
         "gte_four_ancs": gte_four_ancs,
         "non_ems_wro": non_ems_wro,
         "ems_wro": ems_wro,
         "positive_ems_wro": positive_ems_wro,
         "f_births": f_births,
         "c_births": c_births,
         "f_deaths": f_deaths,
         "c_deaths": c_deaths,
         "returned": returned,
         "start_date": start_date,
         "end_date": end_date,
        },
        context_instance=RequestContext(request))
