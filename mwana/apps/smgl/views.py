# vim: ai ts=4 sts=4 et sw=4
import urllib
import datetime

from operator import itemgetter

from django.db.models import Count, Q
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext

from rapidsms.models import Contact
from rapidsms.contrib.messagelog.models import Message

from mwana.apps.contactsplus.models import ContactType
from mwana.apps.help.models import HelpRequest
from mwana.apps.locations.models import Location

from .forms import (StatisticsFilterForm, MotherStatsFilterForm,
    MotherSearchForm, SMSUsersFilterForm, SMSUsersSearchForm, SMSRecordsFilterForm,
    HelpRequestManagerForm)
from .models import (PregnantMother, BirthRegistration, DeathRegistration,
                        FacilityVisit, Referral, ToldReminder,
                        ReminderNotification, SyphilisTest)
from .tables import (PregnantMotherTable, MotherMessageTable, StatisticsTable,
                     StatisticsLinkTable, ReminderStatsTable,
                     SummaryReportTable, ReferralsTable, NotificationsTable,
                     SMSUsersTable, SMSUserMessageTable, SMSRecordsTable,
                     HelpRequestTable)
from .utils import (export_as_csv, filter_by_dates, get_current_district,
    get_location_tree_nodes, percentage, mother_death_ratio, get_default_dates)


def mothers(request):
    province = district = facility = zone = None
    start_date, end_date = get_default_dates()
    edd_start_date = edd_end_date = None

    mothers = PregnantMother.objects.all()

    if request.GET:
        form = MotherStatsFilterForm(request.GET)
        if form.is_valid():
            province = form.cleaned_data.get('province')
            district = form.cleaned_data.get('district')
            facility = form.cleaned_data.get('facility')
            zone = form.cleaned_data.get('zone')
            start_date = form.cleaned_data.get('start_date', start_date)
            end_date = form.cleaned_data.get('end_date', end_date)
            edd_start_date = form.cleaned_data.get('edd_start_date')
            edd_end_date = form.cleaned_data.get('edd_end_date')
    else:
        initial = {
                    'start_date': start_date,
                    'end_date': end_date,
                  }
        form = MotherStatsFilterForm(initial=initial)

    # filter by location if needed...
    locations = Location.objects.all()
    if province:
        locations = get_location_tree_nodes(province)
    if district:
        locations = get_location_tree_nodes(district)
    if facility:
        locations = get_location_tree_nodes(facility)
    if zone:
        locations = [zone]

    mothers = mothers.filter(Q(location__in=locations) | Q(zone__in=locations))

    # filter by created_date
    mothers = filter_by_dates(mothers, 'created_date',
                             start=start_date, end=end_date)
    # filter by EDD
    mothers = filter_by_dates(mothers, 'edd',
                             start=edd_start_date, end=edd_end_date)

    # render as CSV if export
    if form.data.get('export'):
        # The keys must be ordered for the exporter
        keys = ['created_date', 'uid', 'location', 'edd', 'risks']
        records = []
        for mom in mothers:
            created = mom.created_date.strftime('%Y-%m-%d') \
                        if mom.created_date else None
            records.append({
                    'created_date': created,
                    'uid': mom.uid,
                    'location': mom.location,
                    'edd': mom.edd,
                    'risks': ", ".join([x.upper() \
                                     for x in mom.get_risk_reasons()])
                })
        filename = 'summary_report'
        date_range = ''
        edd_date_range = 'ALL'
        if start_date:
            date_range = '_from{0}'.format(start_date)
        if start_date:
            date_range = '{0}_to{1}'.format(date_range, end_date)
        if edd_start_date:
            edd_date_range = '_EDDfrom{0}'.format(edd_start_date)
        if edd_end_date:
            edd_date_range = '{0}_EDDto{1}'.format(edd_date_range, edd_end_date)
        filename = '{0}{1}{2}'.format(filename, date_range, edd_date_range)

        return export_as_csv(records, keys, filename)

    search_form = MotherSearchForm()
    if request.method == 'POST':
        mothers = PregnantMother.objects.all()
        search_form = MotherSearchForm(request.POST)
        uid = request.POST.get('uid', None)
        if uid:
            mothers = mothers.filter(uid__icontains=uid)

    mothers_table = PregnantMotherTable(mothers,
                                        request=request)

    return render_to_response(
        "smgl/mothers.html",
        {"mothers_table": mothers_table,
         "search_form": search_form,
         "form": form
        },
        context_instance=RequestContext(request))


def mother_history(request, id):
    mother = get_object_or_404(PregnantMother, id=id)

    messages = Message.objects.filter(text__icontains=mother.uid,
                                      direction='I')

    # render as CSV if export
    if request.GET.get('export'):
        # The keys must be ordered for the exporter
        keys = ['date', 'msg_type', 'sender', 'facility', 'message']
        records = []
        for msg in messages:
            text = msg.text
            msg_type = text.split(' ')[0].upper()
            records.append({
                    'date': msg.date.strftime('%Y-%m-%d') if msg.date else None,
                    'msg_type': msg_type,
                    'sender': msg.contact,
                    'facility': msg.contact.location.name if msg.contact else '',
                    'message': text
                })
        filename = 'mother{0}_messages_report'.format(mother.uid)

        return export_as_csv(records, keys, filename)

    return render_to_response(
        "smgl/mother_history.html",
        {"mother": mother,
          "message_table": MotherMessageTable(messages,
                                        request=request)
        },
        context_instance=RequestContext(request))


def statistics(request, id=None):
    records = []
    facility_parent = None
    start_date, end_date = get_default_dates()

    province = district = facility = None

    visits = FacilityVisit.objects.all()
    records_for = Location.objects.filter(type__singular='district')

    if id:
        facility_parent = get_object_or_404(Location, id=id)
        # Prepopulate the district
        if not request.GET:
            update = {u'district_0': facility_parent.name,
                      u'district_1': facility_parent.id,
                      u'start_date': start_date,
                      u'end_date': end_date
                      }
            request.GET = request.GET.copy()
            request.GET.update(update)

    if request.GET:
        form = StatisticsFilterForm(request.GET)
        if form.is_valid():
            province = form.cleaned_data.get('province')
            district = form.cleaned_data.get('district')
            facility = form.cleaned_data.get('facility')
            start_date = form.cleaned_data.get('start_date', start_date)
            end_date = form.cleaned_data.get('end_date', end_date)
        # determine what location(s) to include in the report
        if id:
            # get district facilities
            records_for = get_location_tree_nodes(facility_parent, None)
            if district:
                records_for = get_location_tree_nodes(district, None, ~Q(type__slug='zone'))
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
        initial = {
                    'start_date': start_date,
                    'end_date': end_date,
                  }
        form = StatisticsFilterForm(initial=initial)

    for place in records_for:
        locations = Location.objects.all()
        if not id:
            reg_filter = {'district': place}
            visit_filter = {'location__in': [x for x in locations \
                                if get_current_district(x) == place]}
        else:
            reg_filter = {'location': place}
            visit_filter = {'location': place}

        # Get PregnantMother count for each place
        if not id:
            district_facilities = [x for x in locations \
                                if get_current_district(x) == place]
            pregnancies = PregnantMother.objects \
                            .filter(location__in=district_facilities)
        else:
            pregnancies = PregnantMother.objects.filter(location=place)

        pregnancies = filter_by_dates(pregnancies, 'created_date',
                                 start=start_date, end=end_date)

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
        mothers = PregnantMother.objects.filter(id__in=mother_ids)

        anc_visits = mothers.filter(facility_visits__visit_type='anc') \
                            .annotate(Count('facility_visits')) \
                            .values_list('facility_visits__count', flat=True)

        r['anc1'] = r['anc2'] = r['anc3'] = r['anc4'] = 0
        # ANC1 is PregnantMother registrations
        r['pregnancies'] = pregnancies.count()
        r['anc1'] = pregnancies.count()
        num_visits = {}
        for num in anc_visits:
            if num in num_visits:
                num_visits[num] += 1
            else:
                num_visits[num] = 1
        for i in range(1, 4):
            key = 'anc{0}'.format(i + 1)
            if i in num_visits:
                r[key] = num_visits[i]

        pos_visits = mothers.filter(facility_visits__visit_type='pos') \
                            .annotate(Count('facility_visits')) \
                            .values_list('facility_visits__count', flat=True)

        r['pos1'] = r['pos2'] = r['pos3'] = 0
        num_visits = {}
        for num in pos_visits:
            if num in num_visits:
                num_visits[num] += 1
            else:
                num_visits[num] = 1
        for i in range(1, 4):
            key = 'pos{0}'.format(i)
            if i in num_visits:
                r[key] = num_visits[i]

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
        # expunge location_id field
        [x.pop('location_id') for x in records]
        # The keys must be ordered for the exporter
        keys = ['location', 'pregnancies', 'births_com',
                'births_fac', 'births_total',
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
    province = district = facility = None
    start_date, end_date = get_default_dates()

    record_types = ['edd', 'nvd', 'pos', 'ref']
    field_mapper = {'edd': 'Expected Delivery Date', 'nvd': 'Next Visit Date',
                    'pos': 'Post Partem', 'ref': 'Refferals'}

    if request.GET:
        form = StatisticsFilterForm(request.GET)
        if form.is_valid():
            province = form.cleaned_data.get('province')
            district = form.cleaned_data.get('district')
            facility = form.cleaned_data.get('facility')
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')
    else:
        initial = {
                    'start_date': start_date,
                    'end_date': end_date,
                  }
        form = StatisticsFilterForm(initial=initial)

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
        told_mothers = tolds.values_list('mother', flat=True)

        if key == 'edd':
            showed_up = BirthRegistration.objects.filter(
                                                mother__in=reminded_mothers
                                                )
            told_and_showed = showed_up.filter(mother__in=told_mothers)
        elif key == 'ref':
            showed_up = Referral.objects.filter(mother_showed=True,
                                                mother__in=told_mothers
                                                )
            told_and_showed = showed_up.filter(mother__in=told_mothers)

        else:
            showed_up = FacilityVisit.objects.filter(
                                                    mother__in=told_mothers,
                                                    visit_type=key
                                                    )
            told_and_showed = showed_up.filter(mother__in=told_mothers)

        records.append({
                'reminder_type': field_mapper[key],
                'reminders': reminders.count(),
                'showed_up': showed_up.count(),
                'told': tolds.count(),
                'told_and_showed': told_and_showed.count()
            })

    # render as CSV if export
    if form.data.get('export'):
        # The keys must be ordered for the exporter
        keys = ['reminder_type', 'reminders', 'showed_up', 'told', 'told_and_showed']
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
    records = []
    province = district = locations = None
    start_date, end_date = get_default_dates()

    if request.GET:
        form = StatisticsFilterForm(request.GET)
        if form.is_valid():
            province = form.cleaned_data.get('province')
            district = form.cleaned_data.get('district')
            start_date = form.cleaned_data.get('start_date', start_date)
            end_date = form.cleaned_data.get('end_date', end_date)
    else:
        initial = {
                    'start_date': start_date,
                    'end_date': end_date,
                  }
        form = StatisticsFilterForm(initial=initial)

    if province:
        # districts are direct children
        locations = province.location_set.all()
    if district:
        locations = [district]

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

    try:
        cbas = cbas.count()
        clerks = clerks.count()
        workers = workers.count()
    except TypeError:
        cbas = len(cbas)
        clerks = len(clerks)
        workers = len(workers)

    # agregating ANC numbers
    visits = filter_by_dates(FacilityVisit.objects.all(), 'created_date',
                             start=start_date, end=end_date)
    if locations:
        visits = visits.filter(district__in=locations)
    births = filter_by_dates(BirthRegistration.objects.all(), 'date',
                               start=start_date, end=end_date)
    if locations:
        births = births.filter(district__in=locations)

    mother_ids = visits.distinct('mother').values_list('mother', flat=True)
    mothers = PregnantMother.objects.filter(id__in=mother_ids)
    anc_visits = mothers.filter(facility_visits__visit_type='anc') \
                        .annotate(Count('facility_visits')) \
                        .values_list('facility_visits__count', flat=True)
    gte_four_ancs = sum(i >= 4 for i in anc_visits)
    #percentage of women with birth registrations and 4 anc visits
    p_gtefour_ancs = percentage(gte_four_ancs, births.count())

    #number of women with atleast 3 anc visits
    pos_visits = mothers.filter(facility_visits__visit_type='pos') \
                        .annotate(Count('facility_visits')) \
                        .values_list('facility_visits__count', flat=True)
    gte_three_pos = sum(i >= 3 for i in pos_visits)

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

    m_deaths = DeathRegistration.objects.filter(person='ma')
    m_deaths = filter_by_dates(m_deaths, 'date', start=start_date, end=end_date)
    if locations:
        m_deaths = m_deaths.filter(district__in=locations)
    mortality_rate = mother_death_ratio(m_deaths.count(), births.count())

    f_births = percentage(births.filter(place='f').count(), births.count())
    c_births = percentage(births.filter(place='h').count(), births.count())

    deaths = filter_by_dates(DeathRegistration.objects.all(),
                              'date', start=start_date, end=end_date)
    if locations:
        deaths = deaths.filter(district__in=locations)

    f_deaths = deaths.filter(place='f')
    c_deaths = deaths.filter(place='h')

    inf_f_deaths = percentage(f_deaths.filter(person='inf').count(), deaths.count())
    inf_c_deaths = percentage(c_deaths.filter(person='inf').count(), deaths.count())
    ma_f_deaths = percentage(f_deaths.filter(person='ma').count(), deaths.count())
    ma_c_deaths = percentage(c_deaths.filter(person='ma').count(), deaths.count())

    #anc reminders
    reminders = filter_by_dates(ReminderNotification.objects.filter(type='nvd'),
                               'date', start=start_date, end=end_date)
    reminded_mothers = reminders.values_list('mother', flat=True)
    visits = visits.filter(mother__in=reminded_mothers)

    returned = percentage(visits.count(), reminded_mothers.count())

    # syphilis information
    syph_tests = filter_by_dates(SyphilisTest.objects.all(), 'date',
                             start=start_date, end=end_date)
    if locations:
        syph_tests = syph_tests.filter(district__in=locations)

    positive_syphs = syph_tests.filter(result="p")

    positive_syph = percentage(positive_syphs.count(),
                          syph_tests.count())
    positive_mothers = positive_syphs.values_list('mother', flat=True)
    positive_mothers = PregnantMother.objects.filter(id__in=positive_mothers)
    treatments = positive_mothers.annotate(Count('syphilistreatment')) \
                        .values_list('syphilistreatment__count', flat=True)
    positive_syph_completed = sum(i >= 3 for i in treatments)

    records = [
         {'data': "Maternal Mortality Ratio per 100,000",
         'value': mortality_rate},
         {'data': "Number of Clinical Workers Registered",
          'value': workers},
         {'data': "Number of CBAs Registered",
          'value': cbas},
         {'data': "Number of Data Clerks Registered",
          'value': clerks},
         {'data': "Number of Pregnent Mothers Registered",
          'value': mothers.count()},
         {'data': 'Percentage of Women who attended at least 4 ANC visits',
          'value': p_gtefour_ancs},
         {'data': "Percentage of women who returned for ANCs after being reminded",
          'value': returned},
         {'data': 'Number of Women who attended at least 3 POS visits',
          'value': gte_three_pos},
         {'data': "Percentage of non emergency obstetric referral with response and outcome",
          'value': non_ems_wro},
         {'data': "Percentage of emergency obstetric referral with response and outcome",
          'value': ems_wro},
         {'data': "Percentage of positive emergency obstetric referral with response and outcome",
          'value': positive_ems_wro},
         {'data': "Percentage of facility births",
          'value': f_births},
         {'data': "Percentage of community births",
          'value': c_births},
         {'data': "Percentage of Infant facility deaths",
          'value': inf_f_deaths},
         {'data': "Percentage of Infant community deaths",
          'value': inf_c_deaths},
         {'data': "Percentage of Maternal facility deaths",
          'value': ma_f_deaths},
         {'data': "Percentage of Maternal community deaths",
          'value': ma_c_deaths},
         {'data': "Percentage of women who tested positive for Syphilis",
          'value': positive_syph},
         {'data': "Percentage of women tested positive who completed the syphilis treatment",
          'value': positive_syph_completed},
        ]

    # render as CSV if export
    if form.data.get('export'):
        # The keys must be ordered for the exporter
        keys = ['data', 'value']
        filename = 'summary_report'
        date_range = ''
        if start_date:
            date_range = '_from{0}'.format(start_date)
        if start_date:
            date_range = '{0}_to{1}'.format(date_range, end_date)
        filename = '{0}{1}'.format(filename, date_range)
        return export_as_csv(records, keys, filename)

    summary_report_table = SummaryReportTable(records,
                                       request=request)

    return render_to_response(
        "smgl/report.html",
        {"form": form,
         "start_date": start_date,
         "end_date": end_date,
         "summary_report_table": summary_report_table
        },
        context_instance=RequestContext(request))


def notifications(request):
    """
    Report on notifications to help_admin users
    """
    start_date, end_date = get_default_dates()

 #   province = district = facility = None

    help_admins = Contact.objects.filter(is_help_admin=True)
    messages = Message.objects.filter(contact__in=help_admins, direction='O')

    if request.GET:
        form = StatisticsFilterForm(request.GET)
        if form.is_valid():
#            province = form.cleaned_data.get('province')
#            district = form.cleaned_data.get('district')
#            facility = form.cleaned_data.get('facility')
            start_date = form.cleaned_data.get('start_date', start_date)
            end_date = form.cleaned_data.get('end_date', end_date)
    else:
        initial = {
                    'start_date': start_date,
                    'end_date': end_date,
                  }
        form = StatisticsFilterForm(initial=initial)

#    # filter by location if needed...
#    locations = Location.objects.all()
#    if province:
#        locations = get_location_tree_nodes(province)
#    if district:
#        locations = get_location_tree_nodes(district)
#    if facility:
#        locations = get_location_tree_nodes(facility)
#
#    message = messages.filter(from_facility__in=locations)

    # filter by created_date
    messages = filter_by_dates(messages, 'date',
                             start=start_date, end=end_date)

    # render as CSV if export
    if request.GET.get('export'):
        # The keys must be ordered for the exporter
        keys = ['date', 'facility', 'message']
        records = []
        for msg in messages:
            records.append({
                    'date': msg.date.strftime('%Y-%m-%d') if msg.date else None,
                    'facility': msg.contact.location.name if msg.contact else '',
                    'message': msg.text
                })
        filename = 'notifications_report'
        return export_as_csv(records, keys, filename)

    return render_to_response(
        "smgl/notifications.html",
        {"message_table": NotificationsTable(messages,
                                        request=request),
         "form": form
        },
        context_instance=RequestContext(request))


def referrals(request):
    start_date, end_date = get_default_dates()

    province = district = facility = None

    referrals = Referral.objects.all()

    if request.GET:
        form = StatisticsFilterForm(request.GET)
        if form.is_valid():
            province = form.cleaned_data.get('province')
            district = form.cleaned_data.get('district')
            facility = form.cleaned_data.get('facility')
            start_date = form.cleaned_data.get('start_date', start_date)
            end_date = form.cleaned_data.get('end_date', end_date)
    else:
        initial = {
                    'start_date': start_date,
                    'end_date': end_date,
                  }
        form = StatisticsFilterForm(initial=initial)

    # filter by location if needed...
    locations = Location.objects.all()
    if province:
        locations = get_location_tree_nodes(province)
    if district:
        locations = get_location_tree_nodes(district)
    if facility:
        locations = get_location_tree_nodes(facility)

    referrals = referrals.filter(from_facility__in=locations)

    # filter by created_date
    referrals = filter_by_dates(referrals, 'date',
                             start=start_date, end=end_date)

    if request.GET.get('export'):
        # The keys must be ordered for the exporter
        keys = ['date', 'from_facility', 'sender', 'number', 'response',
                'status', 'confirm_amb', 'outcome', 'message']

        records = []
        for ref in referrals:
            contact = ref.session.connection.contact if ref.session.connection else ''
            number = ref.session.connection.identity if ref.session.connection else ''
            message = ref.session.message_incoming.text if ref.session.message_incoming else ''
            records.append({
                    'date': ref.date.strftime('%Y-%m-%d') if ref.date else '',
                    'from_facility': ref.from_facility,
                    'sender': contact,
                    'number': number,
                    'response': "Yes" if ref.responded else "No",
                    'status': ref.status,
                    'confirm_amb': ref.ambulance_response,
                    'outcome': ref.outcome,
                    'message': message
                })
        filename = 'referrals_report'
        return export_as_csv(records, keys, filename)

    return render_to_response(
        "smgl/referrals.html",
        {"message_table": ReferralsTable(referrals,
                                        request=request),
         "form": form,
        },
        context_instance=RequestContext(request))


def sms_records(request):
    """
    Report on all messages
    """
    province = district = facility = keyword = None
    start_date, end_date = get_default_dates()

    if request.GET:
        form = SMSRecordsFilterForm(request.GET)
        if form.is_valid():
            province = form.cleaned_data.get('province')
            district = form.cleaned_data.get('district')
            facility = form.cleaned_data.get('facility')
            start_date = form.cleaned_data.get('start_date', start_date)
            end_date = form.cleaned_data.get('end_date', end_date)
            keyword = form.cleaned_data.get('keyword')
    else:
        initial = {
                    'start_date': start_date,
                    'end_date': end_date,
                  }
        form = SMSRecordsFilterForm(initial=initial)

    # filter by location if needed...
    locations = Location.objects.all()
    if province:
        locations = get_location_tree_nodes(province)
    if district:
        locations = get_location_tree_nodes(district)
    if facility:
        locations = get_location_tree_nodes(facility)

    sms_records = Message.objects.filter(connection__contact__location__in=locations)

    # filter by created_date
    sms_records = filter_by_dates(sms_records, 'date',
                                  start=start_date, end=end_date)

    # filter by keyword
    if keyword:
        sms_records = sms_records.filter(text__istartswith=keyword)

    # render as CSV if export
    if form.data.get('export'):
        # The keys must be ordered for the exporter
        keys = ['date', 'id', 'phone_number', 'msg_type', 'facility', 'text']
        records = []
        for rec in sms_records:
            date = rec.date.strftime('%Y-%m-%d') \
                        if rec.date else None
            records.append({
                    'date': date,
                    'id': rec.id,
                    'phone_number': rec.connection.identity,
                    'msg_type': rec.text.split(' ')[0].upper(),
                    'facility': rec.connection.contact.location if rec.connection.contact else None,
                    'text': (rec.text or '').encode('utf-8'),
                })
        filename = 'sms_records_report'
        date_range = ''
        if start_date:
            date_range = '_from{0}'.format(start_date)
        if start_date:
            date_range = '{0}_to{1}'.format(date_range, end_date)
        filename = '{0}{1}'.format(filename, date_range)

        return export_as_csv(records, keys, filename)

    records_table = SMSRecordsTable(sms_records, request=request)

    return render_to_response(
        "smgl/sms_records.html",
        {"records_table": records_table,
         "form": form
        },
        context_instance=RequestContext(request))

def sms_users(request):
    """
    Report on all users
    """
    start_date, end_date = get_default_dates()
    province = district = c_type = None

    contacts = Contact.objects.all()

    if request.GET:
        form = SMSUsersFilterForm(request.GET)
        if form.is_valid():
            province = form.cleaned_data.get('province')
            district = form.cleaned_data.get('district')
            c_type = form.cleaned_data.get('c_type')
            start_date = form.cleaned_data.get('start_date', start_date)
            end_date = form.cleaned_data.get('end_date', end_date)
    else:
        initial = {
                    'start_date': start_date,
                    'end_date': end_date,
                  }
        form = SMSUsersFilterForm(initial=initial)

    # filter by location if needed...
    locations = Location.objects.all()
    if province:
        locations = get_location_tree_nodes(province)
    if district:
        locations = get_location_tree_nodes(district)

    if c_type:
        contacts = contacts.filter(types__in=[c_type])
    contacts = contacts.filter(location__in=locations)

    # filter by latest_sms_date, which is a property on the model, not a field
    contacts = [x for x in contacts if x.latest_sms_date != None]
    if start_date:
        contacts = [x for x in contacts if x.latest_sms_date.date() >= start_date]
    if end_date:
        contacts = [x for x in contacts if x.latest_sms_date.date() <= end_date]
    contacts = sorted(contacts, key=lambda contact: contact.latest_sms_date, reverse=True)

    # render as CSV if export
    if request.GET.get('export'):
        # The keys must be ordered for the exporter
        keys = ['created_date', 'name', 'number', 'last_active', 'location']
        records = []
        for c in contacts:
            records.append({
                    'created_date': c.created_date.strftime('%Y-%m-%d') if c.created_date else None,
                    'name': c.name.encode('utf-8'),
                    'number': c.default_connection.identity if c.default_connection else None,
                    'last_active': c.latest_sms_date,
                    'location': c.location.name.encode('utf-8') if c.location else '',
                })
        filename = 'sms_users_report'
        return export_as_csv(records, keys, filename)

    search_form = SMSUsersSearchForm()
    if request.method == 'POST':
        contacts = Contact.objects.all()
        search_form = SMSUsersSearchForm(request.POST)
        search_string = request.POST.get('search_string', None)
        if search_string:
            contacts = contacts.filter(Q(name__icontains=search_string) | Q(connection__identity__icontains=search_string))

    return render_to_response(
        "smgl/sms_users.html",
        {"users_table": SMSUsersTable(contacts,
                                        request=request),
         "search_form": search_form,
         "form": form
        },
        context_instance=RequestContext(request))


def sms_user_history(request, id):
    contact = get_object_or_404(Contact, id=id)

    messages = Message.objects.filter(contact=contact,
                                      direction='I')

    # render as CSV if export
    if request.GET.get('export'):
        # The keys must be ordered for the exporter
        keys = ['date', 'msg_type', 'message']
        records = []
        for msg in messages:
            text = msg.text
            msg_type = text.split(' ')[0].upper()
            records.append({
                    'date': msg.date.strftime('%Y-%m-%d') if msg.date else None,
                    'msg_type': msg_type,
                    'message': text
                })
        filename = 'sms_user_{0}_messages_report'.format(contact.name)

        return export_as_csv(records, keys, filename)

    return render_to_response(
        "smgl/sms_user_history.html",
        {"user": contact,
          "message_table": SMSUserMessageTable(messages,
                                        request=request)
        },
        context_instance=RequestContext(request))


def sms_user_statistics(request, id):
    contact = get_object_or_404(Contact, id=id)

    start_date, end_date = get_default_dates()

    if request.GET:
        form = StatisticsFilterForm(request.GET)
        if form.is_valid():
            start_date = form.cleaned_data.get('start_date', start_date)
            end_date = form.cleaned_data.get('end_date', end_date)
    else:
        initial = {
                    'start_date': start_date,
                    'end_date': end_date,
                  }
        form = StatisticsFilterForm(initial=initial)

    mothers = PregnantMother.objects.filter(contact=contact)
    # filter by created_date
    mothers = filter_by_dates(mothers, 'created_date',
                             start=start_date, end=end_date)

    anc_visits = FacilityVisit.objects.filter(contact=contact, visit_type='anc')
    anc_visits = filter_by_dates(anc_visits, 'created_date',
                             start=start_date, end=end_date)

    pos_visits = FacilityVisit.objects.filter(contact=contact, visit_type='pos')
    pos_visits = filter_by_dates(pos_visits, 'created_date',
                             start=start_date, end=end_date)

    births = BirthRegistration.objects.filter(contact=contact)
    births = filter_by_dates(births, 'date',
                             start=start_date, end=end_date)

    deaths = DeathRegistration.objects.filter(contact=contact)
    deaths = filter_by_dates(deaths, 'date',
                             start=start_date, end=end_date)

    query = Q(requested_by__contact=contact) | Q(requested_by__identity=contact.default_connection.identity)

    help_reqs = HelpRequest.objects.filter(query)
    help_reqs = filter_by_dates(help_reqs, 'requested_on',
                             start=start_date, end=end_date)

    tolds = ToldReminder.objects.filter(contact=contact)
    tolds = filter_by_dates(tolds, 'date',
                             start=start_date, end=end_date)

    # Referrals store neither the initiator of the Referral or the initiator of the Referral Outcomes
    # inspect the messagelog
    refs = Message.objects.filter(text__istartswith='REFER ', contact=contact,
                                  direction='I')
    refs = filter_by_dates(refs, 'date',
                             start=start_date, end=end_date)

    ref_outcomes = Message.objects.filter(text__istartswith='REFOUT', contact=contact,
                                  direction='I')
    ref_outcomes = filter_by_dates(ref_outcomes, 'date',
                             start=start_date, end=end_date)

    records = [
         {'data': "Number of Pregnancies registered",
         'value': mothers.count()},
         {'data': "Number of ANC Follow-Up visits registered",
          'value': anc_visits.count()},
         {'data': "Number of POS Follow-Up visits registered",
          'value': pos_visits.count()},
         {'data': "Number of Referrals registereted",
          'value': refs.count()},
         {'data': "Number of Referral Outcomes registered",
          'value': ref_outcomes.count()},
         {'data': 'Number of Births Registered',
          'value': births.count()},
         {'data': 'Number of Deaths Registered',
          'value': deaths.count()},
         {'data': 'Number of Help messages sent',
          'value': help_reqs.count()},
         {'data': 'Number of "TOLD" sent',
          'value': tolds.count()},
        ]

    # render as CSV if export
    if form.data.get('export'):
        # The keys must be ordered for the exporter
        keys = ['data', 'value']
        filename = 'sms_user_summary_report'
        date_range = ''
        if start_date:
            date_range = '_from{0}'.format(start_date)
        if start_date:
            date_range = '{0}_to{1}'.format(date_range, end_date)
        filename = '{0}{1}'.format(filename, date_range)
        return export_as_csv(records, keys, filename)

    summary_report_table = SummaryReportTable(records,
                                       request=request)

    return render_to_response(
        "smgl/sms_user_statistics.html",
        {"user": contact,
         "start_date": start_date,
         "end_date": end_date,
         "summary_report_table": summary_report_table,
         "form": form,
         "user": contact
        },
        context_instance=RequestContext(request))


def help(request):
    province = district = facility = None
    start_date, end_date = get_default_dates()

    help_reqs = HelpRequest.objects.all()

    if request.GET:
        form = StatisticsFilterForm(request.GET)
        if form.is_valid():
            province = form.cleaned_data.get('province')
            district = form.cleaned_data.get('district')
            facility = form.cleaned_data.get('facility')
            start_date = form.cleaned_data.get('start_date', start_date)
            end_date = form.cleaned_data.get('end_date', end_date)
    else:
        initial = {
                    'start_date': start_date,
                    'end_date': end_date,
                  }
        form = StatisticsFilterForm(initial=initial)

    # filter by location if needed...
    locations = Location.objects.all()
    if province:
        locations = get_location_tree_nodes(province)
    if district:
        locations = get_location_tree_nodes(district)
    if facility:
        locations = get_location_tree_nodes(facility)

    help_reqs = help_reqs.filter(requested_by__contact__location__in=locations)

    # filter by created_date
    help_reqs = filter_by_dates(help_reqs, 'requested_on',
                             start=start_date, end=end_date)

    # render as CSV if export
    if form.data.get('export'):
        # The keys must be ordered for the exporter
        keys = ['id', 'requested_on', 'phone', 'name', 'facility',
                'additional_text', 'resolved_by', 'status']
        records = []
        for req in help_reqs:
            requested_on = req.requested_on.strftime('%Y-%m-%d') \
                        if req.requested_on else None
            records.append({
                    'id': req.id,
                    'requested_on': requested_on,
                    'phone': req.requested_by.identity,
                    'name': req.requested_by.contact.name if req.requested_by.contact else None,
                    'facility': req.requested_by.contact.location if req.requested_by.contact else None,
                    'additional_text': req.additional_text,
                    'resolved_by': req.resolved_by,
                    'status': req.get_status_display
                })
        filename = 'help_request_report'
        date_range = ''
        if start_date:
            date_range = '_from{0}'.format(start_date)
        if start_date:
            date_range = '{0}_to{1}'.format(date_range, end_date)
        filename = '{0}{1}'.format(filename, date_range)

        return export_as_csv(records, keys, filename)

    helpreqs_table = HelpRequestTable(help_reqs, request=request)

    return render_to_response(
        "smgl/helprequests.html",
        {"helpreqs_table": helpreqs_table,
         "form": form
        },
        context_instance=RequestContext(request))


def help_manager(request, id):
    help_request = get_object_or_404(HelpRequest, id=id)

    form = HelpRequestManagerForm(request.POST or None, instance=help_request)
    if form.is_valid():
        help_request = form.save()
        now = datetime.datetime.now()
        help_request.addressed_on = now
        help_request.resolved_by = request.user.username
        help_request.status = 'R'
        help_request.save()

    return render_to_response(
        "smgl/helprequest_manager.html",
        {"help_request": help_request,
         "form": form
        },
        context_instance=RequestContext(request))
