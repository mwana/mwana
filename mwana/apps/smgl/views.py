# vim: ai ts=4 sts=4 et sw=4
import urllib
import datetime
import json
from operator import itemgetter
import itertools
from django.db.models import Count, Q
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, DeleteView
from django.core.exceptions import MultipleObjectsReturned

from extra_views import CreateWithInlinesView, UpdateWithInlinesView, InlineFormSet

from rapidsms.models import Contact
from rapidsms.contrib.messagelog.models import Message

from mwana.apps.contactsplus.models import ContactType
from mwana.apps.help.models import HelpRequest
from mwana.apps.locations.models import Location

from .forms import (StatisticsFilterForm, MotherStatsFilterForm,
    MotherSearchForm, SMSUsersFilterForm, SMSUsersSearchForm, SMSRecordsFilterForm,
    HelpRequestManagerForm, SuggestionForm, FileUploadForm, ANCReportForm,
    ReportsFilterForm)

from .models import (PregnantMother, BirthRegistration, DeathRegistration,
                        FacilityVisit,AmbulanceResponse, Referral, ToldReminder,
                        ReminderNotification, SyphilisTest, Suggestion, FileUpload)

from .tables import (PregnantMotherTable, MotherMessageTable, StatisticsTable,
                     StatisticsLinkTable, ReminderStatsTable,
                     SummaryReportTable, ReferralsTable, NotificationsTable,
                     SMSUsersTable, SMSUserMessageTable, SMSRecordsTable,
                     HelpRequestTable, UserReport, get_msg_type,
                     PNCReportTable, ANCDeliveryTable, ReferralReportTable,
                     ErrorTable, ReminderStatsTableSMAG, ReminderStatsTable,
                      ErrorMessageTable, get_response)

from .utils import (export_as_csv, filter_by_dates, get_current_district,
    get_location_tree_nodes, percentage, mother_death_ratio, get_default_dates,
     excel_export_header, write_excel_columns, get_district_facility_zone,
     active_within_messages)
from smsforms.models import XFormsSession
from reminders import SEND_REMINDER_LOWER_BOUND
import xlwt



def fetch_initial(initial, session):
    form_data = session.get('form_data')
    if form_data:
        initial.update(form_data)
    return initial

def save_form_data(cleaned_data, session):
    session['form_data'] = cleaned_data

def anc_report(request, id=None):
    records = []
    facility_parent = None
    start_date, end_date = get_default_dates()
    province = district = facility = None
    visits = FacilityVisit.objects.all()
    records_for = Location.objects.filter(type__singular='district')
    pregnancies = PregnantMother.objects.all()
    filter_option = 'option_1'
    """
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
    """
    if request.GET:
        form = ReportsFilterForm(request.GET)
        if form.is_valid():
            save_form_data(form.cleaned_data, request.session)
            province = form.cleaned_data.get('province')
            district = form.cleaned_data.get('district')
            facility = form.cleaned_data.get('facility')
            start_date = form.cleaned_data.get('start_date', start_date)
            end_date = form.cleaned_data.get('end_date', end_date)
            filter_option = form.cleaned_data.get('filter_option')

            if not start_date:
                start_date, dispose_date = get_default_dates()
            if not end_date:
                dispose_date, end_date = get_default_dates()
        # determine what location(s) to include in the report
        if id:
            # get district facilities
            records_for = get_location_tree_nodes(facility_parent, None)
            if district:
                records_for = get_location_tree_nodes(
                    district, None, ~Q(type__slug='zone')
                    )
                if facility_parent != district:
                    redirect_url = reverse(
                        'district-stats',
                        args=[district.id]
                        )
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
            if facility:
                records_for = [facility]

    else:
        initial = {'start_date': start_date, 'end_date': end_date}
        form = ReportsFilterForm(initial=fetch_initial(initial, request.session))

    for place in records_for:
        locations = Location.objects.all()
        r = {}
        if not id:
            reg_filter = {'location': place}
            visit_filter = {'location__in': get_location_tree_nodes(place)}
        else:
            reg_filter = {'location': place}
            visit_filter = {'location': place}

        # Get PregnantMother count for each place
        if not id:
            district_facilities = get_location_tree_nodes(place)
            pregnancies = PregnantMother.objects \
                            .filter(zone__in=district_facilities)
            births = BirthRegistration.objects \
                            .filter(mother__in=pregnancies)

        else:
            pregnancies = PregnantMother.objects.filter(location=place)
            births = BirthRegistration.objects \
                            .filter(mother__in=pregnancies)

        if filter_option == 'option_1':
            # Option 1 should show All women who have Pregnancy registrations
            #AND gave birth OR had EDD scheduled within our specified time frame
            pregnancies_reg = filter_by_dates(pregnancies, 'created_date',
                start=start_date, end=end_date)
            births = births.filter(mother__in=pregnancies_reg)
            births = filter_by_dates(births, 'date',
                            start=start_date, end=end_date)
            #Get all mothers with birth registrations within the specified time frame.
            birth_mothers = pregnancies_reg.filter(id__in=births.values_list('mother', flat=True))
            #Get all mothers with edd and registration within the specified time frame
            pregnancies_edd = filter_by_dates(pregnancies_reg, 'edd',
                             start=start_date, end=end_date)
            #Combine the two querysets
            pregnancies = birth_mothers | pregnancies_edd
        else:
            # All women who gave birth or had EDD within specified time frame
            pregnancies_edd = filter_by_dates(pregnancies, 'edd',
                             start=start_date, end=end_date)
            births = births.filter(mother__in=pregnancies_edd)
            births = filter_by_dates(births, 'date',
                            start=start_date, end=end_date)
            #Get all mothers with birth registrations within the specified time frame.
            birth_mothers = pregnancies.filter(id__in=births.values_list('mother', flat=True))
            pregnancies = pregnancies_edd | birth_mothers

        r['gestational_age'] = 0
        gestational_ages = 0
        pregnacies_to_calc = 0
        for pregnancy in pregnancies:
            if pregnancy.created_date and pregnancy.lmp:
                gestational_age = pregnancy.created_date.date() - pregnancy.lmp
                if gestational_age.days > 365:
                    pass
                else:
                    gestational_ages += gestational_age.days
                    pregnacies_to_calc += 1
        if pregnacies_to_calc != 0:
            gestational_age = float(gestational_ages)/float(pregnacies_to_calc)
            r['gestational_age'] = "{0:.1f} Weeks".format((gestational_age/7))

        r['location'] = place.name
        r['location_id'] = place.id

        # utilize start/end date if supplied
        if not end_date:
            dispose_date, end_date = get_default_dates()
        r['home'] = births.filter(place='h').count() #home births
        r['facility'] = births.filter(place='f').count() #facility births
        """
        r['unknown'] = pregnancies.exclude(id__in=births.\
            values_list('mother', flat=True)).filter(
            edd__lte=end_date-datetime.timedelta(days=30)).count()
        """
        # Aggregate ANC visits by Mother and # of visits
        #visits = visits.filter(mother__in=pregnancies)
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

    anc_delivery_table = ANCDeliveryTable(records, request=request)
    # disable the link column if on district stats view
    if id:
        anc_delivery_table = ANCDeliveryTable(records, request=request)

    return HttpResponse(anc_delivery_table.as_html())

def pnc_report(request, id=None):
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
        form = ReportsFilterForm(request.GET)
        if form.is_valid():
            save_form_data(form.cleaned_data, request.session)
            province = form.cleaned_data.get('province')
            district = form.cleaned_data.get('district')
            facility = form.cleaned_data.get('facility')
            start_date = form.cleaned_data.get('start_date', start_date)
            end_date = form.cleaned_data.get('end_date', end_date)
        # determine what location(s) to include in the report
            if not start_date:
                start_date, dispose_date = get_default_dates()
            if not end_date:
                dispose_date, end_date = get_default_dates()
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
            if facility:
                records_for = [facility]
    else:
        initial = {
                    'start_date': start_date,
                    'end_date': end_date,
                  }
        form = ReportsFilterForm(initial=fetch_initial(initial, request.session))

    for place in records_for:
        locations = Location.objects.all()
        if not id:
            reg_filter = {'location': place}
            visit_filter = {'location__in': get_location_tree_nodes(place)}
        else:
            reg_filter = {'location': place}
            visit_filter = {'location': place}

        # Get PregnantMother count for each place
        if not id:
            district_facilities = get_location_tree_nodes(place)
            pregnancies = PregnantMother.objects \
                            .filter(zone__in=district_facilities)
            births = BirthRegistration.objects.filter(
                mother__zone__in=district_facilities)
        else:
            pregnancies = PregnantMother.objects.filter(location=place)

        pregnancies = filter_by_dates(pregnancies, 'created_date',
                                 start=start_date, end=end_date)

        r = {'location': place.name}

        r['location_id'] = place.id


        # utilize start/end date if supplied
        if not end_date:
            dispose_date, end_date = get_default_dates()
        births = filter_by_dates(births, 'date',
                                 start=start_date, end=end_date-datetime.timedelta(days=42))
        r['registered_deliveries'] = births.count()
        visits = filter_by_dates(FacilityVisit.objects.filter(visit_type='pos'),
                                'created_date', start=start_date, end=end_date)

        def has_six_day_pnc(birth, visits):
            birth_reg = birth.date
            six_days_later = birth.date + datetime.timedelta(days=6)
            visits = visits.filter(mother=birth.mother,
                created_date__gte=six_days_later-datetime.timedelta(hours=24),
                created_date__lte=six_days_later+datetime.timedelta(hours=24))
            if visits:
                return True
            else:
                return False

        def has_six_week_pnc(birth, visits):
            birth_reg = birth.date
            six_weeks_later = birth.date + datetime.timedelta(days=42)
            visits = visits.filter(mother=birth.mother,
                created_date__gte=six_weeks_later-datetime.timedelta(days=7),
                created_date__lte=six_weeks_later+datetime.timedelta(days=7))
            if visits:
                return True
            else:
                return False

        def pnc_visits(births, visits):
            six_hour_pnc_num = births.count()
            six_day_pnc_num = 0
            six_week_pnc_num = 0
            complete_pnc_num = 0
            for birth in births:
                six_day_pnc = has_six_day_pnc(birth, visits)
                six_week_pnc = has_six_week_pnc(birth, visits)
                if six_day_pnc:
                    six_day_pnc_num += 1
                if six_week_pnc:
                    six_week_pnc_num += 1
                if six_day_pnc_num and six_week_pnc:
                    complete_pnc_num += 1
            return (six_hour_pnc_num, six_day_pnc_num, six_week_pnc_num,
                complete_pnc_num)

        r['six_hour_pnc'], r['six_day_pnc'], r['six_week_pnc'],\
        r['complete_pnc'] = pnc_visits(births, visits)

        deaths = DeathRegistration.objects.filter(**reg_filter)
        deaths = filter_by_dates(deaths, 'date',
                                 start=start_date, end=end_date)

        """
        nmr_deaths = 0
        for death in DeathRegistration.objects.filter(person='inf'):
            try:
                birth = births.filter(mother__uid=death.unique_id)[0]
            except IndexError:
                continue
            time_between = death.date - birth.date
            if time_between.days < 28:
                nmr_deaths += 1
        """

        if nmr_deaths > 0:
            nmr = float(nmr_deaths)/float(births.count())
            nmr = nmr * 1000
            nmr = "{0:.2f}".format(nmr)
        else:
            nmr = '0'

        r['nmr'] = nmr
        r['home'] = births.filter(place='h').count() #home births
        r['facility'] = births.filter(place='f').count() #facility births

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



    statistics_table = StatisticsLinkTable(records,
                                           request=request)
    # disable the link column if on district stats view
    if id:
        statistics_table = StatisticsTable(records,
                                           request=request)

    pnc_report_table = PNCReportTable(records, request=request)
    return HttpResponse(pnc_report_table.as_html())


def referral_report(request):
    start_date, end_date = get_default_dates()
    province = district = facility = None
    referrals = Referral.objects.all()
    if request.GET:
        form = ReportsFilterForm(request.GET)
        if form.is_valid():
            save_form_data(form.cleaned_data, request.session)
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
        form = ReportsFilterForm(initial=fetch_initial(initial, request.session))

    # filter by location if needed...
    locations = Location.objects.all()
    if province:
        locations = get_location_tree_nodes(province)
    if district:
        locations = get_location_tree_nodes(district)

    #if facility:
    #    locations = get_location_tree_nodes(facility)

    referrals = referrals.filter(from_facility__in=locations)

    # filter by created_date
    referrals = filter_by_dates(referrals, 'date',
                             start=start_date, end=end_date)
    ref = {}
    ref_reasons = []
    for short_reason, long_reason in Referral.REFERRAL_REASONS.items():
        if short_reason != 'oth':
            ref_reasons.append(
                (Referral.objects.filter(**{'reason_%s'%short_reason:True }).count(), long_reason)
                )

    sorted_ref_reasons = sorted(ref_reasons, key=lambda item:-item[0])
    most_common_reason = sorted_ref_reasons[0]
    ref['most_common_reason'] = most_common_reason[1]

    ref['referrals'] = referrals.count()

    ref['referral_responses'] = 0
    for referral in referrals:
        if referral.amb_req:
            ref['referral_responses'] += referral.amb_req.ambulanceresponse_set.count()

    ref_with_outcome = referrals.filter(
        responded=True
        )

    ref['referral_response_outcome'] = 0
    for referral in ref_with_outcome:
        if referral.amb_req:
            ref['referral_response_outcome'] += referral.amb_req.ambulanceresponse_set.count()

    ambulance_responses = AmbulanceResponse.objects.filter(
        ambulance_request__referral__in=referrals)
    ambulance_responses = ambulance_responses.filter(response='otw')|ambulance_responses.filter(response='dl')
    ref['transport_by_ambulance'] = ambulance_responses.count()

    total_turnaround_time = 0
    refs_to_count = 0
    for referral in referrals:
        turn_around_time = referral.turn_around_time()
        if turn_around_time:
            refs_to_count += 1
            total_turnaround_time += turn_around_time
    if refs_to_count:
        average_turn_around_secs = float(total_turnaround_time)/float(refs_to_count)
        average_turn_around_hours = average_turn_around_secs/3600
        ref['average_turnaround_time'] = "{0:.1f} Hours".format(average_turn_around_hours)
    else:
        ref['average_turnaround_time'] = 0

    referral_report_table = ReferralReportTable([ref], request=request)
    return HttpResponse(referral_report_table.as_html())

def user_report(request):
    start_date, end_date = get_default_dates()
    contacts = Contact.objects.all()
    province = district = facility = None
    if request.GET:
        form = ReportsFilterForm(request.GET)
        if form.is_valid():
            save_form_data(form.cleaned_data, request.session)
            province = form.cleaned_data.get('province')
            district = form.cleaned_data.get('district')
            facility = form.cleaned_data.get('facility')
            c_type = form.cleaned_data.get('c_type')
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')

            if not start_date:
                start_date, dispose_date = get_default_dates()
            if not end_date:
                dispose_date, end_date = get_default_dates()
    else:
        initial = {
                    'start_date': start_date,
                    'end_date': end_date,
                  }
        form = ReportsFilterForm(initial=fetch_initial(initial, request.session))

    cbas_registered = ContactType.objects.get(slug='cba').contacts.all()
    cbas_registered = filter_by_dates(cbas_registered, 'created_date',
                           end=end_date)
    cbas_active = [cba for cba in cbas_registered if cba.active_status == "active"]
    cbas_active_ids =  Message.objects.filter(
        connection__contact__in=cbas_registered,
        date__gte=start_date-datetime.timedelta(days=60),
        date__lte=end_date).values_list('connection__contact', flat=True).distinct()
    cbas_active = Contact.objects.filter(id__in=cbas_active_ids)


    data_clerks_registered = ContactType.objects.get(slug='dc').contacts.all()
    data_clerks_registered = filter_by_dates(data_clerks_registered, 'created_date',
                              end=end_date)
    data_clerks_active_ids =  Message.objects.filter(
        connection__contact__in=data_clerks_registered,
        date__gte=start_date-datetime.timedelta(days=14),
        date__lte=end_date).values_list('connection__contact', flat=True).distinct()
    data_clerks_active = Contact.objects.filter(id__in=data_clerks_active_ids)


    clinic_worker_types = ContactType.objects.filter(slug__in=['worker'])
    clinic_workers_registered = Contact.objects.filter(types__in=clinic_worker_types)
    clinic_workers_registered = filter_by_dates(clinic_workers_registered, 'created_date',
                              end=end_date)
    clinic_workers_active_ids =  Message.objects.filter(
        connection__contact__in=clinic_workers_registered,
        date__gte=start_date-datetime.timedelta(days=30),
        date__lte=end_date).values_list('connection__contact', flat=True).distinct()
    clinic_workers_active = Contact.objects.filter(id__in=clinic_workers_active_ids)


    #Error rates
    cba_sessions = XFormsSession.objects.filter(connection__contact__types__slug='cba')
    cba_session = cba_sessions.filter(connection__contact__in=cbas_registered)
    cba_errors = cba_sessions.filter(has_error=True)

    workers_sessions = XFormsSession.objects.filter(connection__contact__types__in=clinic_worker_types)
    workers_sessions = workers_sessions.filter(connection__contact__in=clinic_workers_registered)
    workers_errors = workers_sessions.filter(has_error=True)

    data_clerk_sessions = XFormsSession.objects.filter(connection__contact__types__slug='dc')
    data_clerk_sessions = data_clerk_sessions.filter(connection__contact__in=data_clerks_registered)
    data_clerk_errors = data_clerk_sessions.filter(has_error=True)

    locations = Location.objects.all()
    if province:
        locations = get_location_tree_nodes(province)
    if district:
        cbas_registered = [x for x in cbas_registered if x.get_current_district() == district]
        data_clerks_registered = [x for x in data_clerks_registered if x.get_current_district() == district]
        clinic_workers_registered = [x for x in clinic_workers_registered if x.get_current_district() == district]
        cba_errors = [x for x in cba_errors if x.connection.contact.get_current_district() == district]
        workers_errors = [x for x in workers_errors if x.connection.contact.get_current_district() == district]
        data_clerk_errors = [x for x in data_clerk_errors if x.connection.contact.get_current_district() == district]
    if facility:
        cbas_registered = [x for x in cbas_registered if x.get_current_facility() == facility]
        data_clerks_registered = [x for x in data_clerks_registered if x.get_current_facility() == facility]
        clinic_workers_registered = [x for x in clinic_workers_registered if x.get_current_facility() == facility]


    cbas_error_rate = percentage(len(cba_errors), len(cba_sessions))
    clinic_workers_error_rate = percentage(len(workers_errors), len(workers_sessions))
    data_clerks_error_rate = percentage(len(data_clerk_errors), len(data_clerk_sessions))


    try:
        cbas_registered = cbas_registered.count()
        data_clerks_registered = data_clerks_registered.count()
        clinic_workers_registered = clinic_workers_registered.count()
    except TypeError:
        cbas_registered = len(cbas_registered)
        data_clerks_registered = len(data_clerks_registered)
        clinic_workers_registered = len(clinic_workers_registered)

    user_report_table = UserReport([{
               'clinic_workers_registered':clinic_workers_registered,
               'clinic_workers_active': len(clinic_workers_active),
               'data_clerks_registered':data_clerks_registered,
               'data_clerks_active': len(data_clerks_active),
               'cbas_registered': cbas_registered,
               'cbas_active': len(cbas_active),
               'cbas_error_rate': cbas_error_rate,
               'clinic_workers_error_rate': clinic_workers_error_rate,
               'data_clerks_error_rate': data_clerks_error_rate
               }],
               request
               )

    return HttpResponse(user_report_table.as_html())

def get_four_anc_visits(mother):
    mother_visits = mother.facility_visits.filter(visit_type='anc').order_by('visit_date')
    #we should have 3 anc visits if not, we will pad the list of anc visits with
    #null values
    mother_visit_list = list(mother_visits)
    if mother_visits.count() < 3:
        for num in range(mother_visits.count(), 3):
            mother_visit_list.append(None)
    return mother_visit_list


def mothers(request):
    province = district = facility = zone = None
    start_date, end_date = get_default_dates()
    edd_start_date = edd_end_date = None
    mothers = PregnantMother.objects.all()
    if request.GET:
        form = MotherStatsFilterForm(request.GET)
        if form.is_valid():
            #Save the cleaned data into the session
            save_form_data(form.cleaned_data, request.session)

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
        form = MotherStatsFilterForm(initial=fetch_initial(initial, request.session))

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

    if form.data.get('export'):
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet("Mother's Page")
        column_headers = ['Created Date', 'SMN', 'Name', 'District', 'Facility', 'Zone', 'Risk', 'LMP', 'EDD',
                      'Gestational Age', 'Has Delivered', 'NVD2 Date', 'Actual Second ANC Date', 'Second ANC', 'NVD3 Date',
                      'Actual third ANC Date', 'Third ANC', 'NVD4 Date', 'Actual Fourth ANC Date', 'Fourth ANC']
        selected_level = zone or facility or district
        worksheet, row_index = excel_export_header(
                                                   worksheet,
                                                   selected_indicators=column_headers,
                                                   selected_level=selected_level,
                                                   start_date=start_date,
                                                   end_date=end_date
                                                   )
        row_index += 1
        worksheet, row_index = write_excel_columns(worksheet, row_index, column_headers)
        date_format = xlwt.easyxf('align: horiz left;', num_format_str='mm/dd/yyyy')
        worksheet.col(2).width = worksheet.col(3).width = worksheet.col(4).width = worksheet.col(5).width = 20*256
        worksheet.col(9).width = 14*256
        for mother in mothers:
            anc_visits = get_four_anc_visits(mother)
            gestational_age = mother.get_gestational_age()
            has_delivered = mother.has_delivered
            district, facility, zone = get_district_facility_zone(mother.location)
            worksheet.write(row_index, 0, mother.created_date, date_format)
            worksheet.write(row_index, 1, mother.uid)
            worksheet.write(row_index, 2, mother.name)
            worksheet.write(row_index, 3, district)
            worksheet.write(row_index, 4, facility)
            worksheet.write(row_index, 5, mother.zone.name)#somehow the zone fetched using the get_district_facility is wrong
            worksheet.write(row_index, 6, 'Yes' if mother.has_risk_reasons() else 'No')
            worksheet.write(row_index, 7, mother.lmp, date_format)
            worksheet.write(row_index, 8, mother.edd, date_format)

            if gestational_age:
                if gestational_age > 365:
                    worksheet.write(row_index, 9, "Error: Too many days")
                else:
                    worksheet.write(row_index, 9, "{0:.0f} Weeks".format(gestational_age/7)),
            else:
                if has_delivered:
                    worksheet.write(row_index, 9, 'Has Delivered')
                elif not mother.edd:
                    worksheet.write(row_index, 9, 'Error')

            worksheet.write(row_index, 10, 'Yes' if has_delivered else 'No')
            second_anc = anc_visits[0]
            if second_anc:
                worksheet.write(row_index, 11, mother.next_visit, date_format)
                worksheet.write(row_index, 12, second_anc.visit_date, date_format)
                worksheet.write(row_index, 13, 'Yes')
            else:
                worksheet.write(row_index, 11, 'N/A')
                worksheet.write(row_index, 12, 'N/A')
                worksheet.write(row_index, 13, 'No')

            third_anc = anc_visits[1]
            if third_anc:
                worksheet.write(row_index, 14, second_anc.next_visit, date_format)
                worksheet.write(row_index, 15, third_anc.visit_date, date_format)
                worksheet.write(row_index, 16, 'Yes')
            else:
                worksheet.write(row_index, 14, 'N/A')
                worksheet.write(row_index, 15, 'N/A')
                worksheet.write(row_index, 16, 'No')

            fourth_anc = anc_visits[2]
            if fourth_anc:
                worksheet.write(row_index, 17, third_anc.next_visit, date_format)
                worksheet.write(row_index, 18, third_anc.visit_date, date_format)
                worksheet.write(row_index, 19, 'Yes')
            else:
                worksheet.write(row_index, 17, 'N/A')
                worksheet.write(row_index, 18, 'N/A')
                worksheet.write(row_index, 19, 'No')
            row_index += 1

        fname = 'Mothers-export.xls'
        response = HttpResponse(mimetype="applications/vnd.msexcel")
        response['Content-Disposition'] = 'attachment; filename=%s' %fname
        workbook.save(response)
        return response

    """
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
    """


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

    similar_messages = Message.objects.filter(text__icontains=mother.uid,
                                      direction='I')

    #We need to filter out the motherIDs that may be similar to the wanted one
    messages =[]
    for message in similar_messages:
        uid = message.text.split(" ")[1]
        if uid == mother.uid:
            messages.append(message)


    if request.GET.get('export'):
        messages = messages.filter(direction='I') #only show incoming messages.
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet("Mother's Page")
        column_headers = ['Date', 'Time', 'Type', 'SMH', 'Sender Number', 'District', 'Facility', 'Zone', 'Message']
        worksheet, row_index = excel_export_header(
                                                   worksheet,
                                                   selected_indicators=column_headers,
                                                   )
        row_index += 1
        worksheet, row_index = write_excel_columns(worksheet, row_index, column_headers)
        date_format = xlwt.easyxf('align: horiz left;', num_format_str='mm/dd/yyyy')
        time_format = xlwt.easyxf('align: horiz left;', num_format_str='HH:MM:SS')
        worksheet.col(3).width = worksheet.col(4).width = 15*256
        worksheet.col(5).width = worksheet.col(6).width = worksheet.col(7).width = 20*256
        worksheet.col(8).width = 100*256
        for message in messages:
            district, facility, zone = get_district_facility_zone(message.connection.contact.location)
            worksheet.write(row_index, 0, message.date, date_format)
            worksheet.write(row_index, 1, message.date.time(), time_format)
            worksheet.write(row_index, 2, get_msg_type(message))
            worksheet.write(row_index, 3, mother.uid)
            worksheet.write(row_index, 4, message.connection.identity)
            worksheet.write(row_index, 5, district)
            worksheet.write(row_index, 6, facility)
            worksheet.write(row_index, 7, zone)
            worksheet.write(row_index, 8, message.text)
            row_index += 1
        fname = 'Mother-history-export.xls'
        response = HttpResponse(mimetype="applications/vnd.msexcel")
        response['Content-Disposition'] = 'attachment; filename=%s' %fname
        workbook.save(response)
        return response

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
            save_form_data(form.cleaned_data, request.session)
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
        form = StatisticsFilterForm(initial=fetch_initial(initial, request.session))

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

        #add the anc visits
        anc_total = 0
        for num in num_visits:
            anc_total += num_visits[num]
        r['anc_total'] = anc_total

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

        pos_total = 0
        for num in num_visits:
            pos_total += num_visits[num]
        r['pos_total'] = pos_total

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

def reminder_stats(request, smag_table_requested=False):
    mother_records = []
    smag_records = []
    province = district = facility = None
    start_date, end_date = get_default_dates()

    record_types = ['edd', 'anc', 'pos', 'ref']
    field_mapper = {'edd': 'Expected Delivery Date', 'anc': 'ANC',
                    'pos': 'Post Partum', 'ref': 'Referrals',
                    }

    if request.GET:
        form = ReportsFilterForm(request.GET)
        if form.is_valid():
            save_form_data(form.cleaned_data, request.session)
            province = form.cleaned_data.get('province')
            district = form.cleaned_data.get('district')
            facility = form.cleaned_data.get('facility')
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')

            if not start_date:
                start_date, dispose_date = get_default_dates()
            if not end_date:
                dispose_date, end_date = get_default_dates()
    else:
        initial = {
                    'start_date': start_date,
                    'end_date': end_date,
                  }
        form = ReportsFilterForm(initial=fetch_initial(initial, request.session))

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


        # utilize start/end date if supplied
        reminders = filter_by_dates(ReminderNotification.objects.all(), 'date',
                                 start=start_date, end=end_date)
        reminded_mothers = reminders.filter(
            mother__in=mothers).values_list('mother', flat=True)

        tolds = ToldReminder.objects.all()
        referrals = filter_by_dates(Referral.objects.all(), 'date', start=start_date,
            end=end_date)

        births = BirthRegistration.objects.filter(mother__in=mothers)
        births = filter_by_dates(births, 'date', end=end_date, start=start_date)
        if key == 'edd':
            #we want reminders that would have been sent out IF they occur within
            #the selected time period
            #If an edd falls before the start date, not reminder would be
            #scheduled, BUT if edd falls beyond end date then there is a chance we
            #started sending reminders earlier
            scheduled_reminders = filter_by_dates(mothers, 'edd',
                start=start_date,
                end=end_date+datetime.timedelta(days=14))
            scheduled_mothers = scheduled_reminders
            number = scheduled_mothers.distinct()
            sent_reminders= ReminderNotification.objects.filter(
                date__gte=start_date-datetime.timedelta(days=14),
                date__lte=end_date,
                type__icontains='edd_14',
                mother__in=scheduled_mothers)
            birth_anc_pnc_ref = births
            reminded = scheduled_mothers.filter(reminded=True)
            birth_mothers = births.filter(mother__in=scheduled_mothers).values_list('mother', flat=True)
            told_and_showed = ToldReminder.objects.filter(
                type='edd',
                mother__id__in=birth_mothers).count()
            showed_on_time = "N/A"

            #Smag focused
            smag_scheduled_reminders = 0
            for mother in scheduled_mothers:
                smag_scheduled_reminders += mother.get_laycounselors().count()
            smag_number = smag_scheduled_reminders
            smag_sent_reminders = ReminderNotification.objects.filter(
                date__gte=start_date-datetime.timedelta(days=14),
                date__lte=end_date,
                type__icontains='edd_14',
                mother__in=scheduled_mothers)
            smag_tolds = tolds.filter(type__icontains='edd', mother__in=scheduled_mothers).count()
            response_rate = percentage(smag_tolds, smag_sent_reminders.count())
        elif key == 'ref':
            #Mother Focused
            scheduled_mothers = referrals
            scheduled_reminders = scheduled_mothers
            scheduled_mothers  = PregnantMother.objects.filter(
                id__in=scheduled_reminders.values_list('mother', flat=True))
            number = scheduled_mothers.distinct()
            sent_reminders = reminders.filter(
                type='ref',
                mother__in=scheduled_mothers)
            reminded = scheduled_mothers.filter(reminded=True)
            birth_anc_pnc_ref = referrals
            told_mothers = tolds.filter(
                type='ref',
                mother__in=scheduled_mothers
                ).values_list('mother', flat=True)
            told_and_showed = referrals.filter(mother__id__in=told_mothers, mother_showed=True).count()
            showed_on_time = "N/A"


            #smag focused
            smag_scheduled_reminders = 0
            for mother in scheduled_mothers:
                smag_scheduled_reminders += mother.get_laycounselors().count()
            smag_number = smag_scheduled_reminders
            smag_sent_reminders = reminders.filter(
                type__icontains='ref',
                mother__in=scheduled_mothers)
            smag_sent_reminders = ReminderNotification.objects.filter(
                date__gte=start_date-datetime.timedelta(days=7),
                date__lte=end_date,
                type__icontains='ref',
                mother__in=scheduled_mothers)
            smag_tolds = tolds.filter(
                type='ref',
                mother__in=scheduled_mothers).count()
            response_rate = percentage(smag_tolds, smag_sent_reminders.count())
        elif key == 'anc':
            #Mother focused
            scheduled_reminders = FacilityVisit.objects.filter(
                        next_visit__gte=start_date,
                        next_visit__lte=end_date+datetime.timedelta(days=7),
                        visit_type='anc')
            scheduled_mothers  = PregnantMother.objects.filter(
                id__in=scheduled_reminders.values_list('mother', flat=True))
            number = scheduled_mothers.distinct()
            sent_reminders = reminders.filter(
                type='nvd',
                mother__in=scheduled_mothers)
            reminded = scheduled_reminders.filter(reminded=True).values('mother')
            anc = FacilityVisit.objects.filter(
                visit_date__gte=start_date,
                visit_date__lte=end_date)
            birth_anc_pnc_ref = anc
            told_and_showed = 0
            for facility_visit in anc:
                if facility_visit.told():
                    told_and_showed += 1
            showed_on_time = 0
            for visit in anc:
                if visit.is_on_time():
                    showed_on_time += 1

            #SMAG Focused
            smag_scheduled_reminders = 0
            for mother in scheduled_mothers:
                smag_scheduled_reminders += mother.get_laycounselors().count()
            smag_number = smag_scheduled_reminders
            smag_sent_reminders = reminders.filter(
                type='nvd',
                mother__in=scheduled_mothers)
            smag_tolds = 0
            for told in tolds.filter(mother__in=scheduled_mothers):
                if told.get_told_type() == 'anc':
                    smag_tolds += 1
            response_rate = percentage(smag_tolds, smag_sent_reminders.count())
        else:
            #Mother focused
            scheduled_reminders = FacilityVisit.objects.filter(
                        next_visit__gte=start_date,
                        next_visit__lte=end_date+datetime.timedelta(days=7),
                        visit_type='pos')
            scheduled_mothers  = PregnantMother.objects.filter(
                id__in=scheduled_reminders.values_list('mother', flat=True))
            number = scheduled_mothers.distinct()
            sent_reminders = reminders.filter(
                type='pos',
                mother__in=scheduled_mothers)
            reminded = scheduled_reminders.filter(reminded=True).values('mother')
            pos = FacilityVisit.objects.filter(
                visit_date__gte=start_date,
                visit_date__lte=end_date)
            birth_anc_pnc_ref = pos
            told_and_showed = 0
            for facility_visit in anc:
                if facility_visit.told():
                    told_and_showed += 1
            showed_on_time = 0
            for visit in anc:
                if visit.is_on_time():
                    showed_on_time += 1

            #SMAG Focused
            smag_scheduled_reminders = 0
            for mother in scheduled_mothers:
                smag_scheduled_reminders += mother.get_laycounselors().count()
            smag_number = smag_scheduled_reminders
            smag_sent_reminders = reminders.filter(
                type='pos',
                mother__in=scheduled_mothers)
            smag_tolds = 0
            for told in tolds.filter(mother__in=scheduled_mothers):
                if told.get_told_type() == 'pos':
                    smag_tolds += 1
            response_rate = percentage(smag_tolds, smag_sent_reminders.count())

        mother_records.append({
            'reminder_type': field_mapper[key],
            'number':number.count(),
            'scheduled_reminders': scheduled_reminders.count(),
            'sent_reminders': sent_reminders.count(),
            'reminded': reminded.count(),
            'birth_anc_pnc_ref': birth_anc_pnc_ref.count(),
            'told_and_showed': told_and_showed,
            'showed_on_time':showed_on_time
            })
        smag_records.append({
            'reminder_type': field_mapper[key],
            'smag_number':smag_number,
            'smag_scheduled_reminders':smag_scheduled_reminders,
            'smag_sent_reminders': smag_sent_reminders.count(),
            'smag_tolds':smag_tolds,
            'response_rate':response_rate
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

    reminder_mothers_table = ReminderStatsTable(mother_records,
                                           request=request)

    reminder_smag_table = ReminderStatsTableSMAG(smag_records,
                                           request=request)

    if smag_table_requested:
        return HttpResponse(reminder_smag_table.as_html())
    else:
        return HttpResponse(reminder_mothers_table.as_html())

def report(request):
    records = []
    province = district = locations = None
    start_date, end_date = get_default_dates()

    if request.GET:
        form = StatisticsFilterForm(request.GET)
        if form.is_valid():
            save_form_data(form.cleaned_data, request.session)
            province = form.cleaned_data.get('province')
            district = form.cleaned_data.get('district')
            start_date = form.cleaned_data.get('start_date', start_date)
            end_date = form.cleaned_data.get('end_date', end_date)
    else:
        initial = {
                    'start_date': start_date,
                    'end_date': end_date,
                  }
        form = StatisticsFilterForm(initial=fetch_initial(initial, request.session))

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
            save_form_data(form.cleaned_data, request.session)
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
        form = StatisticsFilterForm(initial=fetch_initial(initial, request.session))

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


    if request.GET.get('export'):
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet("Notifications")
        column_headers = ['Date', 'User Number', 'User Name', 'User Type', 'District', 'Facility',
                           'Zone', 'Type of Notification', 'Message']
        worksheet, row_index = excel_export_header(worksheet,
                                                   selected_indicators=column_headers,
                                                   start_date=start_date,
                                                   end_date=end_date
                                                   )
        row_index += 1
        worksheet, row_index = write_excel_columns(worksheet, row_index, column_headers)
        date_format = xlwt.easyxf('align: horiz left;', num_format_str='mm/dd/yyyy')
        row_index += 1
        worksheet.col(1).width = 15*256
        worksheet.col(2).width = 20*256
        worksheet.col(4).width = worksheet.col(5).width = worksheet.col(6).width = 20*256
        worksheet.col(8).width = 100*256
        for message in messages:
            district, facility, zone = get_district_facility_zone(message.connection.contact.location)
            worksheet.write(row_index, 0, message.date, date_format)
            worksheet.write(row_index, 1, message.connection.identity)
            worksheet.write(row_index, 2, message.contact.name)
            worksheet.write(row_index, 3, ", ".join([contact_type.name for contact_type in message.connection.contact.types.all()]))
            worksheet.write(row_index, 4, district)
            worksheet.write(row_index, 5, facility)
            worksheet.write(row_index, 6, zone)
            worksheet.write(row_index, 7, get_msg_type(message))
            worksheet.write(row_index, 8, message.text)
            row_index += 1
        fname = 'notifications-export.xls'
        response = HttpResponse(mimetype="applicatins/vnd.msexcel")
        response['Content-Disposition'] = 'attachment; filename=%s' %fname
        workbook.save(response)
        return response

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
            save_form_data(form.cleaned_data, request.session)
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
        form = StatisticsFilterForm(initial=fetch_initial(initial, request.session))

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
        workbook = xlwt.Workbook(encoding='utf-8')
        time_format = xlwt.easyxf(num_format_str='HH:MM')
        date_format = xlwt.easyxf('align: horiz left;', num_format_str='mm/dd/yyyy')
        worksheet = workbook.add_sheet("Referrals")
        column_headers = ['Date', 'System Timestamp', 'SMH', 'From Facility', 'To Facility', 'Time of Referral', 'Response',
                       'Resp User', 'Confirm AMB', 'Pick', 'Drop', 'Outcome', 'Date Refout', 'Outcome Mother', 'Outcome Baby',
                       'Mode of Delivery']
        selected_level = facility or district or province
        worksheet, row_index = excel_export_header(worksheet,
                                                   selected_indicators=column_headers,
                                                   selected_level=selected_level,
                                                   start_date=start_date,
                                                   end_date=end_date
                                                   )
        row_index += 1
        column_headers[5:5] = ['Cond %s'%cond.title() for cond in Referral.REFERRAL_REASONS.keys()]#Insert the condition columns
        worksheet, row_index = write_excel_columns(worksheet, row_index, column_headers)
        row_index += 1
        for referral in referrals:
            worksheet.write(row_index, 0, referral.date, date_format)
            worksheet.write(row_index, 1, datetime.datetime.now(), date_format)
            worksheet.write(row_index, 2, referral.mother_uid)
            worksheet.write(row_index, 3, referral.from_facility.name)
            worksheet.write(row_index, 4, referral.facility.name)
            #The conditions are a little special in their generation
            column = 5
            for cond in Referral.REFERRAL_REASONS.keys():
                if referral.get_reason(cond):
                    text = 'Yes'
                else:
                    text = 'No'
                worksheet.write(row_index, column, text)
                column += 1
            worksheet.write(row_index, column, referral.time, time_format)
            column += 1
            worksheet.write(row_index, column, "Yes" if referral.responded else "No",)
            column += 1
            worksheet.write(row_index, column, referral.amb_responders())
            column += 1
            worksheet.write(row_index, column, referral.ambulance_response)
            column += 1
            worksheet.write(row_index, column, "")#pick
            column += 1
            worksheet.write(row_index, column, "")#drop
            column += 1
            worksheet.write(row_index, column, referral.outcome)
            column += 1
            worksheet.write(row_index, column, referral.date_outcome, date_format)
            column += 1
            worksheet.write(row_index, column, referral.get_mother_outcome_display())
            column += 1
            worksheet.write(row_index, column, referral.get_baby_outcome_display())
            column += 1
            worksheet.write(row_index, column, referral.get_mode_of_delivery_display())
            row_index += 1

        fname = 'referral-export.xls'
        response = HttpResponse(mimetype="applications/vnd.msexcel")
        response['Content-Disposition'] = 'attachment; filename=%s' %fname
        workbook.save(response)
        return response

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
            save_form_data(form.cleaned_data, request.session)
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
        form = SMSRecordsFilterForm(initial=fetch_initial(initial, request.session))

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


    if form.data.get('export'):
        #import ipdb;ipdb.set_trace()
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet('SMS Users Page')
        selected_level = facility or district or province
        column_headers = column_headers = ['Date', 'Type', 'Incoming or Outgoing', 'User Number', 'User Name',
                                           'User Type', 'District', 'Facility', 'Zone', 'Message']
        keyword = "Keyword: %s"%(keyword if keyword else 'None')
        worksheet, row_index = excel_export_header(worksheet,
                                                   selected_indicators=column_headers,
                                                   selected_level=selected_level,
                                                   start_date=start_date,
                                                   end_date=end_date,
                                                   additional_filters=keyword
                                                   )
        row_index += 1
        worksheet, row_index = write_excel_columns(worksheet, row_index, column_headers)
        date_format = xlwt.easyxf('align: horiz left;', num_format_str='mm/dd/yyyy')

        worksheet.col(3).width = 15*256
        worksheet.col(5).width = 20*256
        worksheet.col(6).width = worksheet.col(7).width = worksheet.col(8).width = 30*256
        worksheet.col(9).width = 100*256

        for message in sms_records:
            district, facility, zone = get_district_facility_zone(message.connection.contact.location)
            worksheet.write(row_index, 0, message.date, date_format)
            worksheet.write(row_index, 1, get_msg_type(message))
            worksheet.write(row_index, 2, message.get_direction_display())
            worksheet.write(row_index, 3, message.connection.identity)
            worksheet.write(row_index, 4, message.connection.contact.name)
            worksheet.write(row_index, 5, ", ".join([contact_type.name for contact_type in message.connection.contact.types.all()]))
            worksheet.write(row_index, 6, district)
            worksheet.write(row_index, 7, facility)
            worksheet.write(row_index, 8, zone)
            worksheet.write(row_index, 9, message.text)
            row_index += 1
        fname = 'sms-records-export.xls'
        response = HttpResponse(mimetype="applications/vnd.msexcel")
        response['Content-Disposition'] = 'attachment; filename=%s' %fname
        workbook.save(response)
        return response

    records_table = SMSRecordsTable(sms_records, request=request)
    records_table.as_html()

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
    province = district = facility = c_type = status = None

    contacts = Contact.objects.all()

    if request.GET:
        form = SMSUsersFilterForm(request.GET)
        if form.is_valid():
            save_form_data(form.cleaned_data, request.session)
            province = form.cleaned_data.get('province')
            district = form.cleaned_data.get('district')
            facility = form.cleaned_data.get('facility')
            c_type = form.cleaned_data.get('c_type')
            status = form.cleaned_data.get('status')
            start_date = form.cleaned_data.get('start_date', start_date)
            end_date = form.cleaned_data.get('end_date', end_date)
    else:
        initial = {
                    'start_date': start_date,
                    'end_date': end_date,
                  }
        form = SMSUsersFilterForm(initial=fetch_initial(initial, request.session))

    # filter by location if needed...
    locations = Location.objects.all()
    if province:
        locations = get_location_tree_nodes(province)
    if district:
        locations = get_location_tree_nodes(district)

    if facility:
        locations = get_location_tree_nodes(facility)

    inactivity_threshold = datetime.timedelta(days=30)
    if c_type:
        contacts = contacts.filter(types__in=[c_type])
        if c_type.slug == "dc":
            inactivity_threshold = datetime.timedelta(days=14)
        elif c_type.slug == "cba":
            inactivity_threshold = datetime.timedelta(days=60)

    contacts = contacts.filter(location__in=locations)

    # filter by latest_sms_date, which is a property on the model, not a field
    active_contacts =  Message.objects.filter(
        date__gte=start_date-inactivity_threshold,
        date__lte=end_date).values_list('connection__contact', flat=True).distinct()
    active_contacts = Contact.objects.filter(id__in=active_contacts)

    inactive_contacts = [x for x in contacts if not x in active_contacts]

    if status == 'active':
        contacts = active_contacts
    elif status == 'inactive':
        contacts = [x for x in inactive_contacts if x.created_date < start_date]

    contacts = [x for x in contacts if x.latest_sms_date]
    contacts = sorted(contacts, key=lambda contact: contact.latest_sms_date, reverse=True)

    if form.data.get('export'):
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet('SMS Users Page')
        selected_level = district or province
        column_headers = column_headers = ['Join Date', 'User Name', 'User Number', 'User Type', 'District',
                                           'Facility', 'Zone', 'Last Active', 'Date Registration', 'Active Status']
        contact_type = "Contact Type: %s"%(c_type if c_type else 'All')
        worksheet, row_index = excel_export_header(worksheet,
                                                   selected_indicators=column_headers,
                                                   selected_level=selected_level,
                                                   start_date=start_date,
                                                   end_date=end_date,
                                                   additional_filters=contact_type
                                                   )
        row_index += 1
        worksheet, row_index = write_excel_columns(worksheet, row_index, column_headers)
        date_format = xlwt.easyxf('align: horiz left;', num_format_str='mm/dd/yyyy')

        worksheet.col(2).width = 15*256
        worksheet.col(4).width = worksheet.col(5).width = worksheet.col(6).width = 30*256

        for contact in contacts:
            district, facility, zone = get_district_facility_zone(contact.location)
            worksheet.write(row_index, 0, contact.created_date, date_format)
            worksheet.write(row_index, 1, contact.name)
            if contact.default_connection:
                worksheet.write(row_index, 2, contact.default_connection.identity)
            else:
                worksheet.write(row_index, 2, "")
            worksheet.write(row_index, 3, ", ".join([contact_type.name for contact_type in contact.types.all()]))
            worksheet.write(row_index, 4, district)
            worksheet.write(row_index, 5, facility)
            worksheet.write(row_index, 6, zone)
            worksheet.write(row_index, 7, contact.latest_sms_date, date_format)
            worksheet.write(row_index, 8, contact.created_date, date_format)
            worksheet.write(row_index, 9, 'Yes' if contact in active_contacts else 'No')
            row_index += 1
        fname = 'sms-users-export.xls'
        response = HttpResponse(mimetype="applications/vnd.msexcel")
        response['Content-Disposition'] = 'attachment; filename=%s' %fname
        workbook.save(response)
        return response

    search_form = SMSUsersSearchForm()
    if request.method == 'POST':
        contacts = Contact.objects.all()
        search_form = SMSUsersSearchForm(request.POST)
        search_string = request.POST.get('search_string', None)
        if search_string:
            contacts = contacts.filter(
                Q(name__icontains=search_string) |
                Q(connection__identity__icontains=search_string)
                )
    users_table = SMSUsersTable(contacts,
        request=request,
        )
    return render_to_response(
        "smgl/sms_users.html",
        {"users_table": users_table,
            "search_form": search_form,
            "form": form
        },
        context_instance=RequestContext(request))


def sms_user_history(request, id):
    contact = get_object_or_404(Contact, id=id)

    messages = Message.objects.filter(contact=contact,
                                      direction='I')

    if request.GET.get('export'):
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet('SMS User Page')
        column_headers = column_headers = ['Join Date', 'User Name', 'User Number', 'User Type', 'Type',
                                           'Message Accepted', 'Message']
        worksheet, row_index = excel_export_header(worksheet,
                                                   selected_indicators=column_headers,
                                                   )
        row_index += 1
        worksheet, row_index = write_excel_columns(worksheet, row_index, column_headers)
        date_format = xlwt.easyxf('align: horiz left;', num_format_str='mm/dd/yyyy')

        worksheet.col(2).width = 15*256
        worksheet.col(6).width = 100*256
        for message in messages:
            try:
                XFormsSession.objects.get(message_incoming=message, has_error=True)
            except XFormsSession.DoesNotExist:
                is_accepted='Yes'
            else:
                is_accepted='No'
            worksheet.write(row_index, 0, message.date, date_format)
            worksheet.write(row_index, 1, contact.name)
            worksheet.write(row_index, 2, contact.default_connection.identity)
            worksheet.write(row_index, 3, ", ".join([contact_type.name for contact_type in contact.types.all()]))
            worksheet.write(row_index, 4, get_msg_type(message))
            worksheet.write(row_index, 5, is_accepted)
            worksheet.write(row_index, 6, message.text)
            row_index += 1
        fname = 'Single-User-export.xls'
        response = HttpResponse(mimetype="applications/vnd.msexcel")
        response['Content-Disposition'] = 'attachment; filename=%s' %fname
        workbook.save(response)
        return response

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
            save_form_data(form.cleaned_data, request.session)
            start_date = form.cleaned_data.get('start_date', start_date)
            end_date = form.cleaned_data.get('end_date', end_date)
    else:
        initial = {
                    'start_date': start_date,
                    'end_date': end_date,
                  }
        form = StatisticsFilterForm(
            initial=fetch_initial(initial, request.session)
            )

    mothers = PregnantMother.objects.filter(contact=contact)
    # filter by created_date
    mothers = filter_by_dates(mothers, 'created_date',
                             start=start_date,
                             end=end_date)

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
    refs = filter_by_dates(refs, 'date', start=start_date, end=end_date)

    ref_outcomes = Message.objects.filter(
        text__istartswith='REFOUT',
        contact=contact,
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
            save_form_data(form.cleaned_data, request.session)
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
        form = StatisticsFilterForm(initial=fetch_initial(initial, request.session))

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

    if form.data.get('export'):
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet('Help')

        selected_level = facility or district or province
        column_headers = ['Date', 'Time', 'User Number', 'User Name', 'User Type', 'District', 'Facility', 'Zone', 'Message',
                          'Resolved Status', 'Date Resolved', 'Time Resolved', 'Resolved by']
        worksheet, row_index = excel_export_header(worksheet,
                                                   selected_indicators=column_headers,
                                                   selected_level=selected_level,
                                                   start_date=start_date,
                                                   end_date=end_date
                                                   )
        row_index += 1
        worksheet, row_index = write_excel_columns(worksheet, row_index, column_headers)
        date_format = xlwt.easyxf('align: horiz left;', num_format_str='mm/dd/yyyy')
        time_format = xlwt.easyxf('align: horiz left;', num_format_str='HH:MM:SS')
        worksheet.col(10).width = worksheet.col(11).width = 11 *256
        worksheet.col(2).width = 15*256
        worksheet.col(3).width = 20*256
        worksheet.col(4).width = 20*256
        worksheet.col(5).width = worksheet.col(6).width = worksheet.col(7).width = 20*256
        worksheet.col(8).width = 100*256
        for help_req in help_reqs:
            district, facility, zone = get_district_facility_zone(help_req.requested_by.contact.location)
            worksheet.write(row_index, 0, help_req.requested_on.date(), date_format)
            worksheet.write(row_index, 1, help_req.requested_on.time(), time_format)
            worksheet.write(row_index, 2, help_req.requested_by.identity)
            worksheet.write(row_index, 3, help_req.requested_by.contact.name)
            worksheet.write(row_index, 4, ", ".join([contact_type.name for contact_type in help_req.requested_by.contact.types.all()]))
            worksheet.write(row_index, 5, district)
            worksheet.write(row_index, 6, facility)
            worksheet.write(row_index, 7, zone)
            worksheet.write(row_index, 8, help_req.additional_text)
            worksheet.write(row_index, 9, help_req.get_status_display)
            worksheet.write(row_index, 10, help_req.addressed_on.date() if help_req.addressed_on else '', date_format)
            worksheet.write(row_index, 11, help_req.addressed_on.time() if help_req.addressed_on else '', time_format)
            worksheet.write(row_index, 12, help_req.resolved_by)
            row_index += 1
        fname = 'help-export.xls'
        response = HttpResponse(mimetype="applications/vnd.msexcel")
        response['Content-Disposition'] = 'attachment; filename=%s' %fname
        workbook.save(response)
        return response


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

def home_page(request):
    if request.is_ajax():
        conditions = (
        ('CSEC', PregnantMother.objects.filter(
            risk_reason_csec=True).count()),
        ('GD', PregnantMother.objects.filter(
            risk_reason_gd=True).count()),
        ('HBP', PregnantMother.objects.filter(
            risk_reason_hbp=True).count()),
        ('PSB', PregnantMother.objects.filter(
            risk_reason_psb=True).count()),
        ('CMP', PregnantMother.objects.filter(
            risk_reason_cmp=True).count()),
        ('Other', PregnantMother.objects.filter(
            risk_reason_oth=True).count()),
        )

        ref_reasons = {}
        for short_reason, long_reason in Referral.REFERRAL_REASONS.items():
            num = Referral.objects.filter(
                **{'reason_%s'%short_reason:True }
                ).count()
            if num > 0: # Only get the ones over 0
                ref_reasons[short_reason.upper()] = num
        num_ref_reasons = sum([cond_num[1] for cond_num in ref_reasons.items()])
        num_mothers = sum([cond_num[1] for cond_num in conditions])
        return HttpResponse(json.dumps(
            {
            'ref_reasons':ref_reasons.items(),
            'num_ref_reasons':num_ref_reasons,
            'conditions':conditions,
            'num_mothers':num_mothers,
            }),
            content_type='application/json')

    today = datetime.datetime.now()
    mubumi_start = datetime.date(2012, 12, 01)
    anc_visits = FacilityVisit.objects.filter(visit_type='anc').order_by('visit_date')
    pos_visits = FacilityVisit.objects.filter(visit_type='pos').order_by('visit_date')
    pregnancies = PregnantMother.objects.order_by('created_date')
    referrals = Referral.objects.order_by('date')

    return render_to_response(
        "smgl/home.html",
        {   'num_emergencies': referrals.count(),
            'num_antenatal': anc_visits.count(),
            'num_postpartum': FacilityVisit.objects.filter(visit_type='pos').count(),
            'num_intrapartum': pregnancies.count(),
            'today': today.strftime('%d %B %Y'),
            'referrals_start':referrals[0].date.strftime('%B %Y'),
            'anc_start':anc_visits[0].visit_date.strftime('%B %Y'),
            'pos_start': pos_visits[0].visit_date.strftime('%B %Y'),
            'pregnancies_start': pregnancies[0].created_date.strftime('%B %Y'),
        },
        context_instance=RequestContext(request)
        )

class SuggestionList(generic.ListView):
    template_name = 'suggestions_list.html'
    model = Suggestion
    context_object_name = "suggestions"

class FileUploadInline(InlineFormSet):
    model = FileUpload
    extra = 1
    def __init__(self, *args, **kwargs):
        self.form_class = FileUploadForm
        return super(FileUploadInline, self).__init__(*args, **kwargs)

class SuggestionEdit(UpdateWithInlinesView):
    template_name = 'smgl/suggestion_form.html'
    model = Suggestion
    form_class = SuggestionForm
    success_url = '/smgl/suggestions'
    inlines = [FileUploadInline,]

    def forms_valid(self, form, inlines):
        form.instance.authors.add(self.request.user)
        for formset in inlines:
            for formset_form in formset.forms:
                formset_form.instance.posted_by = self.request.user
        return super(SuggestionEdit, self).forms_valid(form, inlines)

    def construct_inlines(self):
        inlines = super(SuggestionEdit, self).construct_inlines()
        for formset in inlines:
            for form in formset.forms:
                form.empty_permitted = True
        return inlines

    def get_context_data(self, *args, **kwargs):
        context = super(SuggestionEdit, self).get_context_data(*args, **kwargs)
        context['suggestion'] = self.object
        return context

class SuggestionAdd(CreateWithInlinesView):
    template_name = 'smgl/suggestion_form.html'
    model = Suggestion
    form_class = SuggestionForm
    success_url = '/smgl/suggestions'
    inlines = [FileUploadInline,]

    def forms_valid(self, form, inlines):
        instance = form.instance
        instance.save()
        instance.authors.add(self.request.user)
        for formset in inlines:
            for formset_form in formset.forms:
                formset_form.instance.posted_by = self.request.user
                formset_form.instance.suggestion = form.instance
                formset_form.save()
        return super(SuggestionAdd, self).forms_valid(form, inlines)

    def form_valid(self, form):

        return super(SuggestionAdd, self).form_valid(form)

    def construct_inlines(self):
        inlines = super(SuggestionAdd, self).construct_inlines()
        for formset in inlines:
            for form in formset.forms:
                form.empty_permitted = True
        return inlines

class SuggestionDetail(DetailView):
    model = Suggestion
    context_object_name = "suggestion"

class SuggestionDelete(DeleteView):
    model = Suggestion
    success_url = '/smgl/suggestions'

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(SuggestionDelete, self).dispatch(*args, **kwargs)

def error(request):
    start_date, end_date = get_default_dates()
    province = district = facility = c_type = None
    error_messages = XFormsSession.objects.filter(has_error=True).values_list('message_incoming', flat=True)
    messages = Message.objects.filter(id__in=error_messages).order_by('-date')
    if request.GET:
        form = SMSUsersFilterForm(request.GET)
        if form.is_valid():
            save_form_data(form.cleaned_data, request.session)
            province = form.cleaned_data.get('province')
            district = form.cleaned_data.get('district')
            facility = form.cleaned_data.get('facility')
            c_type = form.cleaned_data.get('c_type')
            start_date = form.cleaned_data.get('start_date', start_date)
            end_date = form.cleaned_data.get('end_date', end_date)
    else:
        initial = {
                    'start_date': start_date,
                    'end_date': end_date,
                  }
        form = SMSUsersFilterForm(initial=fetch_initial(initial, request.session))

    # filter by location if needed...
    locations = Location.objects.all()
    if province:
        locations = get_location_tree_nodes(province)
    if district:
        locations = get_location_tree_nodes(district)
    if facility:
        locations = get_location_tree_nodes(facility)

    messages = messages.filter(connection__contact__location__in=locations)
    if c_type:
        messages = messages.filter(connection__contact__types__in=[c_type])
    messages = filter_by_dates(messages, 'date',
                             start=start_date, end=end_date)


    if request.GET.get('export'):
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet('SMS User Page')
        selected_level = district or province
        column_headers = column_headers = ['Date', 'Type', 'User Number',
            'User Name', 'User Type', 'District',
            'Facility', 'Zone', 'Message', 'Response']
        worksheet, row_index = excel_export_header(worksheet,
                                                   selected_indicators=column_headers,
                                                   start_date=start_date,
                                                   end_date=end_date,
                                                   selected_level=selected_level,
                                                   )
        row_index += 1
        worksheet, row_index = write_excel_columns(worksheet, row_index, column_headers)
        date_format = xlwt.easyxf('align: horiz left;', num_format_str='mm/dd/yyyy')

        worksheet.col(3).width = 15*256
        worksheet.col(8).width = 100*256
        for message in messages:
            contact=message.connection.contact
            district, facility, zone = get_district_facility_zone(contact.location)
            worksheet.write(row_index, 0, message.date, date_format)
            worksheet.write(row_index, 1, get_msg_type(message))
            worksheet.write(row_index, 2, contact.name)
            worksheet.write(row_index, 3, contact.default_connection.identity)
            worksheet.write(row_index, 4, ", ".join([contact_type.name for contact_type in contact.types.all()]))
            worksheet.write(row_index, 5, district)
            worksheet.write(row_index, 6, facility)
            worksheet.write(row_index, 7, zone)
            worksheet.write(row_index, 8, message.text)
            worksheet.write(row_index, 9, get_response(message))
            row_index += 1
        fname = 'Error-Message-export.xls'
        response = HttpResponse(mimetype="applications/vnd.msexcel")
        response['Content-Disposition'] = 'attachment; filename=%s' %fname
        workbook.save(response)
        return response

    search_form = SMSUsersSearchForm()
    if request.method == 'POST':
        messages = Message.objects.filter(id__in=error_messages)
        search_form = SMSUsersSearchForm(request.POST)
        search_string = request.POST.get('search_string', None)
        if search_string:
            messages = messages.filter(
                Q(connection__contact__name__icontains=search_string) |
                Q(connection__identity__icontains=search_string)
                )

    error_table = ErrorTable(messages, request=request)
    return render_to_response(
                              "smgl/errors.html",
                              {
                              "error_table":error_table,
                               "form":form,
                               "search_form":search_form,
                               },
                              context_instance=RequestContext(request))

def error_history(request, id):
    contact = get_object_or_404(Contact, id=id)
    error_messages = XFormsSession.objects.filter(
        has_error=True
        ).values_list('message_incoming', flat=True)
    messages = Message.objects.filter(connection__contact=contact,
                                      direction='I', id__in=error_messages)

    if request.GET.get('export'):
        messages = messages.filter(direction='I') #only show incoming messages.
        workbook = xlwt.Workbook(encoding='utf-8')
        worksheet = workbook.add_sheet("User Page")
        column_headers = ['Date', 'Time', 'Type', 'Sender Number', 'User Type', 'District', 'Facility', 'Zone', 'Message', 'Response']
        worksheet, row_index = excel_export_header(
                                                   worksheet,
                                                   selected_indicators=column_headers,
                                                   )
        row_index += 1
        worksheet, row_index = write_excel_columns(worksheet, row_index, column_headers)
        date_format = xlwt.easyxf('align: horiz left;', num_format_str='mm/dd/yyyy')
        time_format = xlwt.easyxf('align: horiz left;', num_format_str='HH:MM:SS')
        worksheet.col(3).width = worksheet.col(4).width = 15*256
        worksheet.col(5).width = worksheet.col(6).width = worksheet.col(7).width = 20*256
        worksheet.col(8).width = 100*256
        for message in messages:
            district, facility, zone = get_district_facility_zone(message.connection.contact.location)
            worksheet.write(row_index, 0, message.date, date_format)
            worksheet.write(row_index, 1, message.date.time(), time_format)
            worksheet.write(row_index, 2, get_msg_type(message))
            worksheet.write(row_index, 3, message.connection.identity)
            worksheet.write(row_index, 4, ", ".join([contact_type.name for contact_type in message.connection.contact.types.all()]))
            worksheet.write(row_index, 5, district)
            worksheet.write(row_index, 6, facility)
            worksheet.write(row_index, 7, zone)
            worksheet.write(row_index, 8, message.text)
            worksheet.write(row_index, 9, get_response(message))

            row_index += 1
        fname = 'Error-history-export.xls'
        response = HttpResponse(mimetype="applications/vnd.msexcel")
        response['Content-Disposition'] = 'attachment; filename=%s' %fname
        workbook.save(response)
        return response

    return render_to_response(
        "smgl/error_history.html",
        {"user": contact,
          "message_table": ErrorMessageTable(messages,
                                        request=request)
        },
        context_instance=RequestContext(request))


def reports_main(request):
    return render_to_response(
                              "smgl/reports_main.html",
                              context_instance=RequestContext(request))

def reports_tabs(request):
    start_date, end_date = get_default_dates()
    province = district = facility = None
    if request.GET:
        form = ReportsFilterForm(request.GET)
        if form.is_valid():
            save_form_data(form.cleaned_data, request.session)
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
        form = ReportsFilterForm(initial=fetch_initial(initial, request.session))

    return render_to_response(
                            "smgl/reports_tabs.html",
                            {"form": form},
                            context_instance=RequestContext(request))
