# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.reports.models import MessageByLocationUserTypeBackend
from mwana.apps.reports.models import MessageByLocationByBackend
from mwana.apps.reports.models import MessageByLocationByUserType
from mwana.apps.contactsplus.models import ContactType
from datetime import date
from datetime import datetime
from datetime import timedelta

from django.db import connection
from django.db.models import Count
from django.db.models import F
from django.db.models import Q
from django.db.models import Sum
from mwana.apps.labresults.models import Payload
from mwana.apps.labresults.models import Result
from mwana.apps.locations.models import Location
from mwana.apps.patienttracing.models import PatientTrace
from mwana.apps.reminders.models import PatientEvent
from rapidsms.models import Backend


class Expando:
    pass


class GraphService:
    def get_turnarounds(self, start_date, end_date, province_slug, district_slug, facility_slug):
        """
        Uses plain SQL for performance reasons
        """
        sql = _turnaround_query(start_date, end_date, province_slug, district_slug, facility_slug)
        cursor = connection.cursor()
        cursor.execute(sql, [end_date.year, end_date.month])
        category_names = get_category_data(province_slug, district_slug, facility_slug)

        rows = cursor.fetchall()

        transport = []
        processing = []
        delays = []
        retrieving = []
        categories = []
        for row in rows:
            if row[0] in category_names or row[-1] in category_names:
                transport.append(float(row[1]))
                processing.append(float(row[2]))
                delays.append(float(row[3]))
                retrieving.append(float(row[4]))
            if row[-1] in category_names:
                categories.append(str(row[-1]))
            elif row[0] in category_names:
                categories.append(str(row[0]))
        return categories, transport, processing, delays, retrieving

    def get_yearly_supported_sites(self):
        """
        Uses plain SQL for performance/simplicity reasons
        """
        sql = '''
            select reminders."year", eid.eid_count, reminders.remindmi_count  FROM (SELECT extract(year FROM date_logged)::int AS "year",
            count( DISTINCT clinic.id) as remindmi_count FROM reminders_patientevent
            JOIN rapidsms_contact on rapidsms_contact.id = reminders_patientevent.patient_id
            JOIN locations_location as "zone" on zone.id = rapidsms_contact.location_id
            JOIN locations_location as "clinic" on clinic.id = zone.parent_id
            GROUP BY "year") reminders

            FULL JOIN (

            SELECT extract(year FROM result_sent_date)::int AS "year",
            count( DISTINCT clinic_id) AS "eid_count" FROM labresults_result
            WHERE result_sent_date is NOT NULL
            GROUP BY "year") eid on eid."year" = reminders."year"
        '''
        cursor = connection.cursor()
        cursor.execute(sql)

        rows = cursor.fetchall()
        time_ranges = []

        data = {"Results 160": [], "RemindMi": []}
        for row in rows:
            time_ranges.append(row[0])
            data["Results 160"].append(int(row[1]) if row[1] else 0)
            data["RemindMi"].append(int(row[2]) if row[2] else 0)

        return time_ranges, data

    def get_lab_submissions(self, start_date, end_date, province_slug, district_slug, facility_slug):
        facs = get_dbs_facilities(province_slug, district_slug, facility_slug)
        start, end = get_datetime_bounds(start_date, end_date)

        labs = Payload.objects.values_list('source').all().distinct()
        results = Result.objects.filter(payload__incoming_date__gte=start,
                                        payload__incoming_date__lt=end,
                                        clinic__in=facs)

        my_date = date(start_date.year, start_date.month, start_date.day)
        data = {}
        for lab in sorted(labs):
            data[lab[0]] = []
        time_ranges = []
        while my_date <= end_date:
            for lab in sorted(labs):
                data[lab[0]].append(results.filter(
                    payload__incoming_date__year=my_date.year,
                    payload__incoming_date__month=my_date.month,
                    payload__incoming_date__day=my_date.day,
                    payload__source=lab[0]
                ).count())
            time_ranges.append(my_date.strftime('%d %b'))
            my_date = my_date + timedelta(days=1)

        return time_ranges, data

    def get_monthly_lab_submissions(self, start_date, end_date, province_slug, district_slug, facility_slug):
        facs = get_dbs_facilities(province_slug, district_slug, facility_slug)
        start, end = get_datetime_bounds(start_date, end_date)

        labs = Payload.objects.values_list('source').all().distinct()
        results = Result.objects.filter(payload__incoming_date__gte=start,
                                        payload__incoming_date__lt=end,
                                        clinic__in=facs)

        my_date = date(start_date.year, start_date.month, start_date.day)
        data = {}
        for lab in sorted(labs):
            data[lab[0]] = []

        month_ranges = []
        while my_date <= end_date:
            for lab in sorted(labs):
                data[lab[0]].append(results.filter(
                                    payload__incoming_date__year=my_date.year,
                                    payload__incoming_date__month=my_date.month,
                                    payload__source=lab[0]
                                    ).count())
            month_ranges.append(my_date.strftime('%b %Y'))
            my_date = date(my_date.year, my_date.month, 28) + timedelta(days=6)

        return month_ranges, data

    def get_lab_submissions(self, start_date, end_date, province_slug, district_slug, facility_slug):
        """
        Uses raw SQL for performance reasons. Works on PostgreSql database
        """

        labs = Payload.objects.values_list('source').all().distinct()

        ids = ", ".join("%s" % fac.id for fac in get_dbs_facilities(province_slug, district_slug, facility_slug))
        if not ids:
            ids = '-1'

        query = '''
        select count(labresults_result.id), incoming_date::date  as my_date, source from labresults_result
        join labresults_payload on labresults_payload.id = labresults_result.payload_id
        join locations_location loc on loc.id = clinic_id
        where loc.id in (''' + ids + ''')
        and date(incoming_date) between %s and %s
        group by source, my_date'''

        cursor = connection.cursor()
        cursor.execute(query, [start_date, end_date])
        rows = cursor.fetchall()

        objects = []
        for row in rows:
            count, my_date, source = row
            expando = Expando()
            expando.count = int(count)
            expando.my_date = my_date
            expando.source = source
            objects.append(expando)

        my_date = date(start_date.year, start_date.month, start_date.day)
        data = {}
        for lab in sorted(labs):
            data[lab[0]] = []

        time_ranges = []
        while my_date <= end_date:
            for lab in sorted(labs):
                item = [x for x in objects if
                        (x.source == lab[0] and x.my_date == my_date)]
                count = 0
                if item:
                    count = item[0].count
                data[lab[0]].append(count)
            time_ranges.append(my_date.strftime('%d %b'))
            my_date = my_date + timedelta(days=1)

        return time_ranges, data

    def get_monthly_lab_submissions(self, start_date, end_date, province_slug, district_slug, facility_slug):
        """
        Uses raw SQL for performance reasons. Works on PostgreSql database
        """

        labs = Payload.objects.values_list('source').all().distinct()

        ids = ", ".join("%s" % fac.id for fac in get_dbs_facilities(province_slug, district_slug, facility_slug))
        if not ids:
            ids = '-1'

        query = '''select count(labresults_result.id), year(incoming_date) as year,
        month(incoming_date) as month, source from labresults_result
        join labresults_payload on labresults_payload.id = labresults_result.payload_id
        join locations_location loc on loc.id = clinic_id
        where loc.id in (''' + ids + ''')
        and date(incoming_date) between %s and %s
        group by source, year, month'''

        cursor = connection.cursor()
        cursor.execute(query, [start_date, end_date])
        rows = cursor.fetchall()

        objects = []
        for row in rows:
            count, year, month, source = row
            expando = Expando()
            expando.count = int(count)
            expando.year = year
            expando.month = month
            expando.source = source
            objects.append(expando)

        my_date = date(start_date.year, start_date.month, start_date.day)
        data = {}
        for lab in sorted(labs):
            data[lab[0]] = []

        month_ranges = []
        while my_date <= end_date:
            for lab in sorted(labs):
                item = [x for x in objects if
                        (x.source == lab[0] and x.year == my_date.year and x.month == my_date.month)]
                count = 0
                if item:
                    count = item[0].count
                data[lab[0]].append(count)
            month_ranges.append(my_date.strftime('%b %Y'))
            my_date = date(my_date.year, my_date.month, 28) + timedelta(days=6)

        return month_ranges, data

    def get_monthly_birth_trends(self, start_date, end_date, province_slug, district_slug, facility_slug):
        facs = get_facilities(province_slug, district_slug, facility_slug)
        start, end = get_datetime_bounds(start_date, end_date)

        trend_items = ['Facility births', 'Community births', 'Unspecified']
        births = PatientEvent.objects.filter(Q(date__gte=start),
                                             Q(date__lt=end),
                                             (Q(patient__location__parent__in=facs) |
                                              Q(patient__location__in=facs))
        )

        my_date = date(start_date.year, start_date.month, start_date.day)
        data = {}
        for item in sorted(trend_items):
            data[item] = []

        births_map = {'Facility births':'cl', 'Community births':'hm', 'Unspecified':None}

        month_ranges = []
        while my_date <= end_date:
            for item in sorted(trend_items):
                data[item].append(births.filter(
                    date__year=my_date.year,
                    date__month=my_date.month,
                    event_location_type=births_map[item]
                ).count())
            month_ranges.append(my_date.strftime('%b %Y'))
            my_date = date(my_date.year, my_date.month, 28) + timedelta(days=6)

        return month_ranges, data

    def get_monthly_scheduled_visit_trends(self, start_date, end_date,
    province_slug, district_slug, facility_slug, visit_type="6 day", data_type="count"):
        facs = get_facilities(province_slug, district_slug, facility_slug)
        start, end = get_datetime_bounds(start_date, end_date)

        trend_map = {'Mother not Reminded by CBA': ['new'],
                     'Mother  reminded by CBA': ['told', 'confirmed'],
                     'Mother  has gone to clinic': ['confirmed'],
                     " Total Births": ['new', 'told', 'confirmed'],
        }
        trend_items = [key for key in trend_map]

        reminders = PatientTrace.objects.filter(Q(start_date__gte=start),
                                                Q(start_date__lt=end),
                                                Q(initiator='automated_task'),
                                                Q(type=visit_type),
                                                (Q(patient_event__patient__location__parent__in=facs) |
                                                 Q(patient_event__patient__location__in=facs))
        )

        my_date = date(start_date.year, start_date.month, start_date.day)
        data = {}
        for item in sorted(trend_items):
            data[item] = []

        month_ranges = []

        while my_date <= end_date:
            divisor = 1
            if data_type.lower() == "percentage":
                divisor = reminders.filter(
                    start_date__year=my_date.year,
                    start_date__month=my_date.month,
                    status__in=['new', 'told', 'confirmed']
                                  ).count()/100.0
            for item in sorted(trend_items):
                data[item].append(round(reminders.filter(
                    start_date__year=my_date.year,
                    start_date__month=my_date.month,
                    status__in=trend_map[item]
                                  ).count()/(divisor or 1), 1))

            month_ranges.append(my_date.strftime('%b %Y'))
            my_date = date(my_date.year, my_date.month, 28) + timedelta(days=6)

        return month_ranges, data

    def get_monthly_turnaround_trends(self, start_date, end_date, province_slug, district_slug, facility_slug):
        facs = get_dbs_facilities(province_slug, district_slug, facility_slug)
        start, end = get_datetime_bounds(start_date, end_date)

        trend_items = ['Turnaround Time', '1. Transport Time', '2. Processing Time',
                       '3. Delays at Lab', '4. Retrieval Time']

        my_date = date(start_date.year, start_date.month, start_date.day)
        data = {}
        for item in sorted(trend_items):
            data[item] = []

        results = Result.objects.filter(clinic__in=facs, notification_status='sent')

        month_ranges = []
        while my_date <= end_date:
            tt_res = results.filter(result_sent_date__year=my_date.year,
                                    result_sent_date__month=my_date.month,
                                    collected_on__lte=F('result_sent_date')
            )
            tt_diff = 0.0
            tt = max(1, len(tt_res))
            for result in tt_res:
                tt_diff = 1 + tt_diff + (result.result_sent_date.date() - result.collected_on).days

            data['Turnaround Time'].append(int(tt_diff / tt))

            #Transport Time
            tt_res = results.filter(result_sent_date__year=my_date.year,
                                    result_sent_date__month=my_date.month,
                                    collected_on__lte=F('entered_on')
            )
            tt_diff = 0.0
            tt = max(1, len(tt_res))
            for result in tt_res:
                tt_diff = tt_diff + (result.entered_on - result.collected_on).days

            data['1. Transport Time'].append(int(tt_diff / tt))

            #Processing Time
            tt_res = results.filter(result_sent_date__year=my_date.year,
                                    result_sent_date__month=my_date.month,
                                    entered_on__lte=F('processed_on')
            )
            tt_diff = 0.0
            tt = max(1, len(tt_res))
            for result in tt_res:
                tt_diff = 1 + tt_diff + (result.processed_on - result.entered_on).days

            data['2. Processing Time'].append(int(tt_diff / tt))

            #Delays at Lab
            tt_res = results.filter(result_sent_date__year=my_date.year,
                                    result_sent_date__month=my_date.month,
                                    processed_on__lte=F('arrival_date')
            )
            tt_diff = 0.0
            tt = max(1, len(tt_res))
            for result in tt_res:
                tt_diff = tt_diff + (result.arrival_date.date() - result.processed_on).days

            data['3. Delays at Lab'].append(int(tt_diff / tt))

            #Retrieval Time
            tt_res = results.filter(result_sent_date__year=my_date.year,
                                    result_sent_date__month=my_date.month,
                                    arrival_date__lte=F('result_sent_date')
            )
            tt_diff = 0.0
            tt = max(1, len(tt_res))
            for result in tt_res:
                tt_diff = 1 + tt_diff + (result.result_sent_date - result.arrival_date).days

            data['4. Retrieval Time'].append(int(tt_diff / tt))

            month_ranges.append(my_date.strftime('%b %Y'))
            my_date = date(my_date.year, my_date.month, 28) + timedelta(days=6)

        return month_ranges, data


    def get_monthly_dbs_testing_trends(self, start_date, end_date, province_slug, district_slug, facility_slug):
        facs = get_dbs_facilities(province_slug, district_slug, facility_slug)
        start, end = get_datetime_bounds(start_date, end_date)

        trend_items = ['1. Collected at Facility', '2. Received at Lab',
                       '3. Tested at Lab']

        my_date = date(start_date.year, start_date.month, start_date.day)
        data = {}
        for item in sorted(trend_items):
            data[item] = []

        results = Result.objects.filter(clinic__in=facs)

        month_ranges = []
        while my_date <= end_date:
            tt_res = results.filter(collected_on__year=my_date.year,
                                    collected_on__month=my_date.month).filter(
                collected_on__lte=F('entered_on')
            ).count()

            data['1. Collected at Facility'].append(tt_res)

            #Processing Time
            tt_res = results.filter(entered_on__year=my_date.year,
                                    entered_on__month=my_date.month
            ).count()

            data['2. Received at Lab'].append(tt_res)

            #Processing Time
            tt_res = results.filter(processed_on__year=my_date.year,
                                    processed_on__month=my_date.month,
                                    entered_on__lte=F('arrival_date')
            ).count()

            data['3. Tested at Lab'].append(tt_res)

            month_ranges.append(my_date.strftime('%b %Y'))
            my_date = date(my_date.year, my_date.month, 28) + timedelta(days=6)

        return month_ranges, data

    def get_monthly_results_retrival_trends(self, start_date, end_date, province_slug, district_slug, facility_slug):
        facs = get_dbs_facilities(province_slug, district_slug, facility_slug)
        start, end = get_datetime_bounds(start_date, end_date)

        my_date = date(start_date.year, start_date.month, start_date.day)
        data = {}
        trend_items = ['Facilities', "Negative", "Positive", "Rejected", 'Total Results']
        for item in sorted(trend_items):
            data[item] = []

        results = Result.objects.filter(clinic__in=facs,
                                        result_sent_date__gte=start,
                                        result_sent_date__lte=end)

        month_ranges = []
        while my_date <= end_date:
            tt_res = results.filter(result_sent_date__year=my_date.year,
                                    result_sent_date__month=my_date.month
            )
            neg_res = results.filter(result_sent_date__year=my_date.year,
                                     result_sent_date__month=my_date.month,
                                     result='N'
                                     ).count()
            pos_res = results.filter(result_sent_date__year=my_date.year,
                                     result_sent_date__month=my_date.month,
                                     result='P'
                                     ).count()
            rej_res = results.filter(result_sent_date__year=my_date.year,
                                     result_sent_date__month=my_date.month,
                                     result__in=['R', 'I', 'X']
                                     ).count()

            data['Negative'].append(neg_res)
            data['Positive'].append(pos_res)
            data['Rejected'].append(rej_res)
            data['Total Results'].append(len(tt_res))
            tt_clinics = len(set([res.clinic for res in tt_res]))

            data['Facilities'].append(tt_clinics)

            month_ranges.append(my_date.strftime('%b %Y'))
            my_date = date(my_date.year, my_date.month, 28) + timedelta(days=6)

        return month_ranges, data

    def get_monthly_messages(self, start_date, end_date,
                             province_slug, district_slug, facility_slug, data_type="count", direction='all'):
        use_percentage = "count" != data_type
        field = "count"
        if direction == 'I':
            field = "count_incoming"
        elif direction == 'O':
            field = "count_outgoing"

        start, end = get_datetime_bounds(start_date, end_date)

        groups = Backend.objects.exclude(name__iexact="Message_Tester").values_list('name').all().distinct()
        messages = MessageByLocationByBackend.objects.filter(min_date__gte=start,
                                                             min_date__lt=end)

        if any([province_slug, district_slug, facility_slug]):
            facs = get_sms_facilities(province_slug, district_slug, facility_slug)
            messages = MessageByLocationByBackend.objects.filter(min_date__gte=start,
                                                                 min_date__lt=end, absolute_location__in=facs)

        my_date = date(start_date.year, start_date.month, start_date.day)
        data = {}
        for item in sorted(groups):
            data[item[0]] = []

        month_ranges = []

        while my_date <= end_date:
            denom = messages.filter(year=my_date.year,
                                    month=my_date.month).aggregate(sum=Sum(field))['sum'] or 0
            for item in sorted(groups):
                if use_percentage:
                    num = messages.filter(year=my_date.year,
                                          month=my_date.month,
                                          backend=item[0]).aggregate(sum=Sum(field))['sum'] or 0

                    data[item[0]].append(round(100.0 * num/(denom or 1), 1))
                else:
                    data[item[0]].append(
                        messages.filter(year=my_date.year,
                                        month=my_date.month,
                                        backend=item[0]).aggregate(sum=Sum(field))['sum'] or 0)

            month_ranges.append(my_date.strftime('%b %Y'))
            my_date = date(my_date.year, my_date.month, 28) + timedelta(days=6)

        return month_ranges, data


    def get_monthly_messages_by_usertype(self, start_date, end_date,
    province_slug, district_slug, facility_slug, data_type="count", direction='all'):
        use_percentage = "count" != data_type
        field = "count"
        if direction == 'I':
            field = "count_incoming"
        elif direction == 'O':
            field = "count_outgoing"

        start, end = get_datetime_bounds(start_date, end_date)

        contact_types = ContactType.objects.exclude(slug='patient').values_list('slug').all().distinct()
        messages = MessageByLocationByUserType.objects.filter(min_date__gte=start,
                                                              min_date__lt=end)

        if any([province_slug, district_slug, facility_slug]):
            facs = get_sms_facilities(province_slug, district_slug, facility_slug)
            messages = MessageByLocationByUserType.objects.filter(min_date__gte=start,
                                                                  min_date__lt=end, absolute_location__in=facs)

        my_date = date(start_date.year, start_date.month, start_date.day)
        data = {}
        for item in sorted(contact_types):
            data[item[0]] = []

        month_ranges = []

        while my_date <= end_date:
            denom = messages.filter(year=my_date.year,
                                    month=my_date.month).aggregate(sum=Sum(field))['sum'] or 0
            for item in sorted(contact_types):
                if use_percentage:
                    num = messages.filter(year=my_date.year,
                                          month=my_date.month,
                                          worker_type=item[0]).aggregate(sum=Sum(field))['sum'] or 0

                    data[item[0]].append(round(100.0 * num/(denom or 1), 1))
                else:
                    data[item[0]].append(
                        messages.filter(year=my_date.year,
                                        month=my_date.month,
                                        worker_type=item[0]).aggregate(sum=Sum(field))['sum'] or 0)

            month_ranges.append(my_date.strftime('%b %Y'))
            my_date = date(my_date.year, my_date.month, 28) + timedelta(days=6)

        return month_ranges, data

    def get_monthly_messages_by_partner(self, start_date, end_date,
    province_slug, district_slug, facility_slug, data_type="count", direction='all'):
        # TODO: Consider moving this function to another module
        use_percentage = False

        start, end = get_datetime_bounds(start_date, end_date)
        all_messages = MessageByLocationUserTypeBackend.objects.exclude(backend="message_tester").filter(min_date__gte=start,
            min_date__lt=end)

        if any([province_slug, district_slug, facility_slug]):
            facs = get_sms_facilities(province_slug, district_slug, facility_slug)
            all_messages = all_messages.filter(absolute_location__in=facs)

        my_date = date(start_date.year, start_date.month, start_date.day)
        partner_names = ['TDRC-Clinic-I', 'TDRC-Clinic-O', 'Participant-O', 'Others-I', 'Others-O']
        backend_names = ['mtn', 'mtn-modem', 'zain', 'zain-smpp']

        if backend_names != [str(b.name) for b in Backend.objects.exclude(name='message_tester')]:
            raise Exception('Backend list is inconsistent')
        partners = []
        for p in partner_names:
            for b in backend_names:
                partners.append("%s:%s" % (b, p))

        data = {}
        for item in partners:
            data[item] = []

        month_ranges = []

        while my_date <= end_date:
            for backend in backend_names:
                backend_messages = all_messages.filter(backend=backend)
                denom_in = backend_messages.filter(year=my_date.year,
                                                   month=my_date.month).aggregate(sum=Sum('count_incoming'))['sum'] or 0
                denom_out = backend_messages.filter(year=my_date.year,
                                                              month=my_date.month).aggregate(sum=Sum('count_outgoing'))['sum'] or 0
                tdrc_vl_notification = backend_messages.filter(year=my_date.year,
                            month=my_date.month).aggregate(sum=Sum('count_vl_notification'))['sum'] or 0

                tdrc_dbs_notification = backend_messages.filter(year=my_date.year,
                            month=my_date.month).aggregate(sum=Sum('count_dbs2_notification'))['sum'] or 0

                other_dbs_notification = backend_messages.filter(year=my_date.year,
                            month=my_date.month).aggregate(sum=Sum('count_DBS_notification'))['sum'] or 0
                all_worker_messages_in = backend_messages.filter(year=my_date.year,
                                                                 month=my_date.month,
                                                          worker_type__contains='worker').aggregate(sum=Sum('count_incoming'))['sum'] or 0
                all_worker_messages_out = backend_messages.filter(year=my_date.year,
                                                                  month=my_date.month,
                                                          worker_type__contains='worker').aggregate(sum=Sum('count_outgoing'))['sum'] or 0
                ratio_sum = tdrc_vl_notification + tdrc_dbs_notification + other_dbs_notification
                projected_tdrc_vl_messages_in = 0
                projected_tdrc_vl_messages_out = 0
                projected_tdrc_dbs_messages_in = 0
                projected_tdrc_dbs_messages_out = 0
                projected_tdrc_clinic_messages_in = 0
                projected_tdrc_clinic_messages_out = 0

                #                tdrc_participant_message_out = Message.objects.filter(date__year=my_date.year, direction='O', connection__backend__name=backend).filter(
                #                                                          date__month=my_date.month, text__icontains='Bring your referral letter with you').count()
                tdrc_participant_message_out = backend_messages.filter(year=my_date.year,
                            month=my_date.month).aggregate(sum=Sum('count_participant_notification'))['sum'] or 0

                other_projected_in = 0
                other_projected_out = 0
                if ratio_sum:
                    projected_tdrc_vl_messages_in = all_worker_messages_in * tdrc_vl_notification / (1.0 * ratio_sum )
                    projected_tdrc_vl_messages_out = all_worker_messages_out * tdrc_vl_notification / (1.0 * ratio_sum )
                    projected_tdrc_dbs_messages_in = all_worker_messages_in * tdrc_dbs_notification / (1.0 * ratio_sum )
                    projected_tdrc_dbs_messages_out = all_worker_messages_out * tdrc_dbs_notification / (1.0 * ratio_sum )
                    other_projected_in = denom_in - int(projected_tdrc_dbs_messages_in) - int(projected_tdrc_vl_messages_in)
                    other_projected_out = denom_out - tdrc_participant_message_out - int(projected_tdrc_dbs_messages_out) - int(projected_tdrc_vl_messages_out)
                    projected_tdrc_clinic_messages_in = projected_tdrc_vl_messages_in + projected_tdrc_dbs_messages_in
                    projected_tdrc_clinic_messages_out = projected_tdrc_vl_messages_out + projected_tdrc_dbs_messages_out

                if use_percentage:
                    data['%s:TDRC-Clinic-I' % backend].append(round(100.0 * projected_tdrc_clinic_messages_in/(denom_in or 1), 1))
                    data['%s:TDRC-Clinic-O' % backend].append(round(100.0 * projected_tdrc_clinic_messages_out/(denom_out or 1), 1))
                    data['%s:Others-I' % backend].append(round(100.0 * other_projected_in/(denom_in or 1), 1))
                    data['%s:Others-O' % backend].append(round(100.0 * other_projected_out/(denom_out or 1), 1))
                    data['%s:Participant-O' % backend].append(round(100.0 * tdrc_participant_message_out/(denom_out or 1), 1))
                else:
                    data['%s:TDRC-Clinic-I' % backend].append(round(projected_tdrc_clinic_messages_in))
                    data['%s:TDRC-Clinic-O' % backend].append(round(projected_tdrc_clinic_messages_out))
                    data['%s:Others-I' % backend].append(round(other_projected_in))
                    data['%s:Others-O' % backend].append(round(other_projected_out))
                    data['%s:Participant-O' % backend].append(round(tdrc_participant_message_out))
            month_ranges.append(my_date.strftime('%b %Y'))
            my_date = date(my_date.year, my_date.month, 28) + timedelta(days=6)

        return month_ranges, data

    def get_facility_vs_community(self, start_date, end_date, province_slug, district_slug, facility_slug):
        facs = get_facilities(province_slug, district_slug, facility_slug)
        start, end = get_datetime_bounds(start_date, end_date)

        return PatientEvent.objects.filter(date__gte=start,
                                           date__lt=end,
                                           patient__location__parent__in=facs,
                                           event__name__iexact='birth').\
            values('event_location_type').\
            annotate(total=Count('id'))

    def get_messages_by_location(self, start_date, end_date, province_slug, district_slug, facility_slug):

        start, end = get_datetime_bounds(start_date, end_date)
        messages = MessageByLocationByUserType.objects.filter(min_date__gte=start).filter(max_date__lte=end)
        report_level = 'province'

        if district_slug:
            report_level = 'facility'
            messages = messages.filter(district_slug=district_slug)
        elif province_slug:
            report_level = 'district'
            messages = messages.filter(province_slug=province_slug)

        return report_level, 'sum', messages.values(report_level).annotate(sum=Sum('count'))


def _turnaround_query(start_date, end_date, province_slug, district_slug, facility_slug):
    """
        Uses raw SQL for performance reasons. Works on PostgreSql database
    """
    ids = ", ".join("%s" % fac.id for fac in get_dbs_facilities(province_slug, district_slug, facility_slug))
    if not ids:
        ids = '-1'

    select_clause  = '''select name, avg(transport_time), avg(processing_time), avg(delays_at_lab), avg(retrieving_time) from (
            SELECT province."name", entered_on-collected_on as transport_time, processed_on - entered_on as processing_time
            ,arrival_date::date-processed_on as delays_at_lab,
            result_sent_date::date - arrival_date::date as retrieving_time'''

    join_clause = ''' FROM labresults_result
            join locations_location as facility on facility.id=clinic_id
            join locations_location as district on district.id = facility.parent_id
            join locations_location as province on province.id = district.parent_id
            where collected_on <= processed_on
            and entered_on <= processed_on
            and arrival_date >= processed_on
            and notification_status <> 'obsolete'
            and extract(year from result_sent_date) = %s
            and extract(month from result_sent_date) = %s
            and facility.id in (''' + ids + ''')
            ) a
            '''

    aggregate_clause = '''
            group by name
            order by name
            '''

    if province_slug or district_slug or facility_slug:
        select_clause = select_clause.replace('from (', ', district from (') + ', district."name" as district'
        aggregate_clause = '''
            group by name, district
            order by district
            '''

    if district_slug or facility_slug:
        select_clause = select_clause.replace('from (', ', facility from (')  + ', facility.name as facility'
        aggregate_clause = '''group by name, district, facility
            order by facility
            '''

    return select_clause + join_clause + aggregate_clause


def get_category_data(province_slug, district_slug, facility_slug):
    facs = Location.objects.filter(supportedlocation__supported=True).exclude(lab_results=None).\
        exclude(name__icontains='training').exclude(name__icontains='support')
    if facility_slug:
        return [loc.name for loc in facs.filter(slug=facility_slug)]
    elif district_slug:
        return list(set([loc.name for loc in facs.filter(parent__slug=district_slug)]))
    elif province_slug:
        return list(set([loc.parent.name for loc in facs.filter(parent__parent__slug=province_slug)]))
    else:
        return list(set([loc.parent.parent.name for loc in facs.all()]))


def get_datetime_bounds(start_date, end_date):
    return datetime(start_date.year, start_date.month, start_date.day), \
           datetime(end_date.year, end_date.month, end_date.day) + \
           timedelta(days=1)


def get_facilities(province_slug, district_slug, facility_slug):
    facs = Location.objects.filter(supportedlocation__supported=True).\
        exclude(name__icontains='training').exclude(name__icontains='support')
    if facility_slug:
        facs = facs.filter(slug=facility_slug)
    elif district_slug:
        facs = facs.filter(parent__slug=district_slug)
    elif province_slug:
        facs = facs.filter(parent__parent__slug=province_slug)
    return facs


def get_sms_facilities(province_slug, district_slug, facility_slug):
    facs = Location.objects.all().\
        exclude(name__icontains='training').exclude(name__icontains='support')
    if facility_slug:
        facs = facs.filter(Q(slug=facility_slug) | Q(parent__slug=facility_slug))
    elif district_slug:
        facs = facs.filter(Q(parent__parent__slug=district_slug) | Q(parent__slug=district_slug) | Q(slug=district_slug))
    elif province_slug:
        facs = facs.filter(Q(parent__parent__parent__slug=province_slug) | Q(parent__parent__slug=province_slug) | Q(parent__slug=province_slug) | Q(slug=province_slug))
    return facs


def get_dbs_facilities(province_slug, district_slug, facility_slug):
    return get_facilities(province_slug, district_slug, facility_slug).exclude(lab_results=None)
