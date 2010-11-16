from operator import itemgetter

from datetime import date
from datetime import datetime
from datetime import timedelta
from django.db import connection
from django.db.models import Q
from django.db.models import Sum
from mwana import const
from mwana.apps.labresults.models import Result
from mwana.apps.labresults.models import SampleNotification
from mwana.apps.locations.models import Location

class Results160Reports:
    STATUS_CHOICES = ('in-transit', 'unprocessed', 'new', 'notified', 'sent', 'updated')
    # Arbitrary values
    SOME_INVALID_DAYS = 3650
    MAX_REPORTING_PERIOD = 100 # days
    BAR_LENGTH = 5.0
    today = date.today()
    dbsr_enddate = datetime(today.year, today.month, today.day) + timedelta(days=1)
    -timedelta(seconds=0.01)
    dbsr_startdate = datetime(today.year, today.month, today.day)-timedelta(days=30)

    def safe_rounding(self, float):
        try:
            return int(round(float))
        except TypeError:
            return None

    def set_reporting_period(self, startdate, enddate):
        if startdate:
            self.dbsr_startdate = datetime(startdate.year, startdate.month,
                                           startdate.day)
        if enddate:
            self.dbsr_enddate = \
            datetime(enddate.year, enddate.month, enddate.day)\
            + timedelta(days=1) - timedelta(seconds=0.01)

    def get_active_facilities(self):
        return Location.objects.filter(lab_results__notification_status__in=
                                       ['sent']).distinct()

    def get_facilities_for_dbs_notifications(self):
        return Location.objects.filter(supportedlocation__supported=True,
                                       samplenotification__date__gte=self.dbsr_startdate,
                                       samplenotification__date__lte=self.dbsr_enddate
                                       ).distinct()

    def get_facilities_for_rsts_reporting(self):
        return Location.objects.filter(lab_results__notification_status__in=['sent'],
                                       lab_results__result_sent_date__gte=self.dbsr_startdate,
                                       lab_results__result_sent_date__lte=self.dbsr_enddate
                                       ).distinct()

    def get_facilities_for_transport_reporting(self):
        return Location.objects.filter(lab_results__collected_on__lte=self.dbsr_enddate,
                                       lab_results__entered_on__gte=self.dbsr_startdate,
                                       lab_results__entered_on__lte=self.dbsr_enddate
                                       ).distinct()

    def get_facilities_for_processing_reporting(self):
        return Location.objects.filter(Q(lab_results__entered_on__lt=self.dbsr_enddate) |
                                       Q(lab_results__entered_on=self.dbsr_enddate),
                                       Q(lab_results__processed_on__gt=self.dbsr_startdate)
                                       | Q(lab_results__processed_on=self.dbsr_startdate),
                                       Q(lab_results__processed_on__lt=self.dbsr_enddate) |
                                       Q(lab_results__processed_on=self.dbsr_enddate)
                                       ).distinct()

    def get_facilities_for_turnarround_reporting(self):
        return Location.objects.filter(Q(lab_results__collected_on__lt=self.dbsr_enddate) |
                                       Q(lab_results__collected_on=self.dbsr_enddate),
                                       Q(lab_results__result_sent_date__gt=self.dbsr_startdate)
                                       | Q(lab_results__result_sent_date=self.dbsr_startdate),
                                       Q(lab_results__result_sent_date__lt=self.dbsr_enddate) |
                                       Q(lab_results__result_sent_date=self.dbsr_enddate)
                                       ).distinct()

    def get_facilities_for_entering_reporting(self):
        return Location.objects.filter(lab_results__entered_on__lte=self.dbsr_enddate,
                                       lab_results__result_sent_date__gte=self.dbsr_startdate,
                                       lab_results__result_sent_date__lte=self.dbsr_enddate
                                       ).distinct()

    def get_facilities_for_retrieval_reporting(self):
        return Location.objects.filter(lab_results__arrival_date__lte=self.dbsr_enddate,
                                       lab_results__result_sent_date__gte=self.dbsr_startdate,
                                       lab_results__result_sent_date__lte=self.dbsr_enddate
                                       ).distinct()

    def get_facilities_for_samples_at_lab(self):
        return Location.objects.filter(Q(lab_results__notification_status__in=self.STATUS_CHOICES),
                                       Q(lab_results__entered_on__gt=self.dbsr_startdate)
                                       | Q(lab_results__entered_on=self.dbsr_startdate),
                                       Q(lab_results__entered_on__lt=self.dbsr_enddate) |
                                       Q(lab_results__entered_on=self.dbsr_enddate)
                                       ).distinct()

    def get_facilities_for_pending_rsts(self):
        return Location.objects.filter(Q(lab_results__notification_status__in=[
                                       'unprocessed', 'new', 'notified', 'updated'])
                                       ).distinct()


    def get_results_by_status(self, status):
        """Returns results query set by status in reporting period"""
        
        return Result.objects.filter(Q(result_sent_date__gt=self.dbsr_startdate)
                                     | Q(result_sent_date=self.dbsr_startdate),
                                     Q(result_sent_date__lt=self.dbsr_enddate) |
                                     Q(result_sent_date=self.dbsr_enddate))\
            .filter(notification_status__in
                    =status)

    def get_results_by_status_and_location(self, status, location):
        """Returns results query set by status in reporting period"""
        return Result.objects.filter(notification_status__in=status, clinic=location)


    def get_sent_results(self, location):
        """Returns results query set for sent results in reporting period"""
        return Result.objects.filter(Q(result_sent_date__gt=self.dbsr_startdate)
                                     | Q(result_sent_date=self.dbsr_startdate),
                                     Q(result_sent_date__lt=self.dbsr_enddate) |
                                     Q(result_sent_date=self.dbsr_enddate))\
            .filter(clinic=location,
                    notification_status='sent')

    def get_avg_dbs_turnaround_time(self, location):
        results = Result.objects.filter(Q(collected_on__lt=self.dbsr_enddate) |
                                        Q(collected_on=self.dbsr_enddate),
                                        Q(result_sent_date__gt=self.dbsr_startdate)
                                        | Q(result_sent_date=self.dbsr_startdate),
                                        Q(result_sent_date__lt=self.dbsr_enddate) |
                                        Q(result_sent_date=self.dbsr_enddate))\
            .filter(clinic=location,
                    notification_status='sent')
        if not results:
            return (0, None)
        tt_diff = 0.0
        for result in results:
            tt_diff = 1 + tt_diff + (result.result_sent_date.date() - result.collected_on).days
        return (results.count(), tt_diff / results.count())

    def get_avg_rsts_entering_time(self, location):
        results = Result.objects.filter(clinic=location,
                                        processed_on__lte=self.dbsr_enddate,
                                        result_sent_date__gte=self.dbsr_startdate,
                                        result_sent_date__lte=self.dbsr_enddate)
            
        if not results:
            return (0, None)
        tt_diff = 0.0
        for result in results:
            tt_diff = 1 + tt_diff + (result.arrival_date.date() - result.processed_on).days
        return (results.count(), tt_diff / results.count())

    def get_avg_dbs_retrieval_time(self, location):
        results = Result.objects.filter(arrival_date__lte=self.dbsr_enddate,
                                        result_sent_date__gte=self.dbsr_startdate,
                                        result_sent_date__lte=self.dbsr_enddate)\
        .filter(clinic=location,
                notification_status='sent')
        if not results:
            return (0, None)
        tt_diff = 0.0
        for result in results:
            tt_diff = 1 + tt_diff + (result.result_sent_date.date() - result.arrival_date.date()).days
        return (results.count(), tt_diff / results.count())

    def get_avg_dbs_processing_time(self, location):
        results = Result.objects.filter(Q(processed_on__gt=self.dbsr_startdate)
                                        | Q(processed_on=self.dbsr_startdate),
                                        Q(processed_on__lt=self.dbsr_enddate) |
                                        Q(processed_on=self.dbsr_enddate))\
        .filter(clinic=location)
        if not results:
            return (0, None)
        tt_diff = 0.0
        for result in results:
            tt_diff = 1 + tt_diff + (result.processed_on - result.entered_on).days
        return (results.count(), tt_diff / results.count())

    def get_avg_dbs_transport_time(self, location):
        results = Result.objects.filter(Q(collected_on__lt=self.dbsr_enddate) |
                                        Q(collected_on=self.dbsr_enddate),
                                        Q(entered_on__gt=self.dbsr_startdate)
                                        | Q(entered_on=self.dbsr_startdate),
                                        Q(entered_on__lt=self.dbsr_enddate) |
                                        Q(entered_on=self.dbsr_enddate))\
        .filter(clinic=location)
        if not results:
            return (0, None)
        tt_diff = 0.0
        for result in results:
            tt_diff = 1 + tt_diff + (result.entered_on - result.collected_on).days
        return (results.count(), tt_diff / results.count())

    # Reports
    def dbs_payloads_report(self, startdate=None, enddate=None):
        self.set_reporting_period(startdate, enddate)
        table = []
        
        table.append(['  Source Lab', 'Count'])

        cursor = connection.cursor()
        cursor.execute('select source, count(*) as count from \
             labresults_payload where incoming_date BETWEEN %s AND %s group by \
             source', [self.dbsr_startdate, self.dbsr_enddate])
        total = 0
        for row in cursor.fetchall():
            total = total + row[1]
            table.append([' ' + row[0], row[1]])
        table.append(['All listed sources', total])
        return sorted(table, key=lambda table: table[0].lower())

    def dbs_pending_results_report(self, startdate=None, enddate=None):
        self.set_reporting_period(startdate, enddate)
        table = []

        table.append(['  District', '  Facility', 'New', 'Notified', 'Updated',
                     'Unprocessed', 'Total Pending'])
        new = notified = updated = unprocessed = total = 0
        tt_new = tt_notified = tt_updated = tt_unprocessed = tt_total = 0
        for location in self.get_facilities_for_pending_rsts():
            new = self.get_results_by_status_and_location(['new'], location).count()
            notified = self.get_results_by_status_and_location(['notified'], location).count()
            updated = self.get_results_by_status_and_location(['updated'], location).count()
            unprocessed = self.get_results_by_status_and_location(['unprocessed'], location).count()
            total = self.get_results_by_status_and_location(['updated', 'new',
                                                            'notified', 'unprocessed'], location).count()
            district_name = location.parent and location.parent.name or ' '
            table.append([' ' + district_name, ' ' + location.name,\
                          new, notified, updated, unprocessed, total])
            tt_new = tt_new + new
            tt_notified = tt_notified + notified
            tt_updated = tt_updated + updated
            tt_unprocessed = tt_unprocessed + unprocessed
            tt_total = tt_total + total
            
        table.append(['All listed districts', 'All listed  clinics', tt_new, tt_notified, tt_updated, tt_unprocessed, tt_total])
        return sorted(table, key=itemgetter(0, 1))

    def dbs_sample_notifications_report(self, startdate=None, enddate=None):
        self.set_reporting_period(startdate, enddate)
        table = []
        table.append(['  District', '  Facility', 'Samples'])
        reported = 0
        tt_reported = 0
        for location in self.get_facilities_for_dbs_notifications():
            reported = SampleNotification.objects.filter(Q(location=location),
                                                         Q(date__gt=self.dbsr_startdate)
                                                         | Q(date=self.dbsr_startdate),
                                                         Q(date__lt=self.dbsr_enddate) |
                                                         Q(date=self.dbsr_enddate)).\
            aggregate(sum=Sum("count"))['sum']
                
            tt_reported = tt_reported + reported
            table.append([' ' + location.parent.name, ' ' + location.name, reported])
        table.append(['All listed districts', 'All listed  clinics', tt_reported])
        return sorted(table, key=itemgetter(0, 1))

    def dbs_samples_at_lab_report(self, startdate=None, enddate=None):
        self.set_reporting_period(startdate, enddate)
        table = []

        table.append(['  District', '  Facility', 'Samples'])

        received = 0
        tt_received = 0
        for location in self.get_facilities_for_samples_at_lab():
            received = Result.objects.filter(clinic=location,
                                             entered_on__gte=self.dbsr_startdate,
                                             entered_on__lt=self.dbsr_enddate).count()
            tt_received = tt_received + received

            table.append([' ' + location.parent.name, ' ' + location.name, received, ])
        table.append(['All listed districts', 'All listed  clinics', tt_received])
        return sorted(table, key=itemgetter(0, 1))

    def dbs_sent_results_report(self, startdate=None, enddate=None):
        self.set_reporting_period(startdate, enddate)
        table = []

        table.append(['  District', '  Facility',
                     'Positive', 'Negative', 'Rejected', 'Total Received'])
        tt_positive = tt_negative = tt_rejected = tt_total = 0
        positive = negative = rejected = total = 0
        for location in self.get_facilities_for_rsts_reporting():
            positive = self.get_sent_results(location).filter(result='P').count()
            negative = self.get_sent_results(location).filter(result='N').count()
            rejected = self.get_sent_results(location).filter(result__in=['R', 'X', 'I']).count()
            total = self.get_sent_results(location).count()

            table.append([' ' + location.parent.name, ' ' + location.name, positive,
                         negative, rejected, total,])

            tt_positive = tt_positive + positive
            tt_negative = tt_negative + negative
            tt_rejected = tt_rejected + rejected
            tt_total = tt_total + total
        table.append(['All listed districts', 'All listed  clinics', tt_positive, tt_negative, tt_rejected, tt_total])
        return sorted(table, key=itemgetter(0, 1))

    def dbs_avg_turnaround_time_report(self, startdate=None, enddate=None):
        """
        Returns the average number of days (INCLUSIVE) from the day DBS are
        collected at the facilities to day results for these samples are
        received back at the facilities
        """
        self.set_reporting_period(startdate, enddate)
        table = []

        table.append(['  District', '  Facility', 'Results', 'Turnaround (Days)'])
        days = number_sent = 0
        sum_days = tt_number_sent = 0
        min_days = self.SOME_INVALID_DAYS
        max_days = None

        locations = self.get_facilities_for_turnarround_reporting()
        for location in locations:
            number_sent, days = self.get_avg_dbs_turnaround_time(location)
            tt_number_sent = tt_number_sent + number_sent
            sum_days = sum_days + days
            min_days = min(days, min_days)
            max_days = max(days, max_days)

            table.append([' ' + location.parent.name, ' ' + location.name,
                         number_sent, self.safe_rounding(days)])

        avg = None
        if locations:
            avg = sum_days / locations.count()
        if min_days == self.SOME_INVALID_DAYS:
            min_days = None

        table.append(['All listed districts', 'All listed  clinics', tt_number_sent, self.safe_rounding(avg)])
        return self.safe_rounding(min_days), self.safe_rounding(max_days), self.safe_rounding(tt_number_sent), locations.count(), \
            sorted(table, key=itemgetter(0, 1))

    def dbs_avg_entering_time_report(self, startdate=None, enddate=None):
        """
        Returns the average number of days (INCLUSIVE) from the day results are
        tested to the day are updated in the machine at the lab
        """
        self.set_reporting_period(startdate, enddate)
        table = []

        table.append(['  District', '  Facility', 'Results', 'Entering Time(Days)'])
        days = number_entered = 0
        sum_days = tt_number_entered = 0
        min_days = self.SOME_INVALID_DAYS
        max_days = None

        locations = self.get_facilities_for_entering_reporting()
        for location in locations:
            number_entered, days = self.get_avg_rsts_entering_time(location)
            tt_number_entered = tt_number_entered + number_entered
            sum_days = sum_days + days
            min_days = min(days, min_days)
            max_days = max(days, max_days)

            table.append([' ' + location.parent.name, ' ' + location.name,
                         number_entered, self.safe_rounding(days)])

        avg = None
        if locations:
            avg = sum_days / locations.count()
        if min_days == self.SOME_INVALID_DAYS:
            min_days = None

        table.append(['All listed districts', 'All listed  clinics', tt_number_entered, self.safe_rounding(avg)])
        return self.safe_rounding(min_days), self.safe_rounding(max_days), self.safe_rounding(tt_number_entered), locations.count(), \
            sorted(table, key=itemgetter(0, 1))

    def dbs_avg_retrieval_time_report(self, startdate=None, enddate=None):
        """
        Returns the average number of days (INCLUSIVE) from the day tested
        results are updated to the day are sent to the facilities
        """
        self.set_reporting_period(startdate, enddate)
        table = []

        table.append(['  District', '  Facility', 'Results', 'Retieval Time(Days)'])
        days = number_sent = 0
        sum_days = tt_number_sent = 0
        min_days = self.SOME_INVALID_DAYS
        max_days = None

        locations = self.get_facilities_for_retrieval_reporting()
        for location in locations:
            number_sent, days = self.get_avg_dbs_retrieval_time(location)
            tt_number_sent = tt_number_sent + number_sent
            sum_days = sum_days + days
            min_days = min(days, min_days)
            max_days = max(days, max_days)

            table.append([' ' + location.parent.name, ' ' + location.name,
                         number_sent, self.safe_rounding(days)])

        avg = None
        if locations:
            avg = sum_days / locations.count()
        if min_days == self.SOME_INVALID_DAYS:
            min_days = None

        table.append(['All listed districts', 'All listed  clinics', tt_number_sent, self.safe_rounding(avg)])
        return self.safe_rounding(min_days), self.safe_rounding(max_days), self.safe_rounding(tt_number_sent), locations.count(), \
            sorted(table, key=itemgetter(0, 1))

    def dbs_avg_processing_time_report(self, startdate=None, enddate=None):
        """
        Returns the average number of days (INCLUSIVE) from the day DBS arrive
        at the labs to the day they are tested
        """
        self.set_reporting_period(startdate, enddate)
        table = []

        table.append(['  District', '  Facility', 'Results', 'Processing Time (Days)'])
        days = number_processed = 0
        sum_days = tt_number_processed = 0
        min_days = self.SOME_INVALID_DAYS
        max_days = None

        locations = self.get_facilities_for_processing_reporting()
        for location in locations:
            number_processed, days = self.get_avg_dbs_processing_time(location)
            tt_number_processed = tt_number_processed + number_processed
            sum_days = sum_days + days
            min_days = min(days, min_days)
            max_days = max(days, max_days)

            table.append([' ' + location.parent.name, ' ' + location.name,
                         number_processed, self.safe_rounding(days)])

        avg = None
        if locations:
            avg = sum_days / locations.count()
        if min_days == self.SOME_INVALID_DAYS:
            min_days = None

        table.append(['All listed districts', 'All listed  clinics', tt_number_processed, self.safe_rounding(avg)])
        return self.safe_rounding(min_days), self.safe_rounding(max_days), self.safe_rounding(tt_number_processed), locations.count(), \
            sorted(table, key=itemgetter(0, 1))


    def dbs_avg_transport_time_report(self, startdate=None, enddate=None):
        """
        Returns the average number of days (INCLUSIVE) from the day DBS are
        collected at the facilities to the day they arrive at the labs
        """
        self.set_reporting_period(startdate, enddate)
        table = []

        table.append(['  District', '  Facility', 'DBS', 'Transport Time (Days)'])
        days = number_sent = 0
        sum_days = tt_samples = 0
        min_days = self.SOME_INVALID_DAYS
        max_days = None

        locations = self.get_facilities_for_transport_reporting()
        for location in locations:
            number_sent, days = self.get_avg_dbs_transport_time(location)
            tt_samples = tt_samples + number_sent
            sum_days = sum_days + days
            min_days = min(days, min_days)
            max_days = max(days, max_days)

            table.append([' ' + location.parent.name, ' ' + location.name,
                         number_sent, self.safe_rounding(days)])

        avg = None
        if locations:
            avg = sum_days / locations.count()
        if min_days == self.SOME_INVALID_DAYS:
            min_days = None

        table.append(['All listed districts', 'All listed  clinics', tt_samples, self.safe_rounding(avg)])
        return self.safe_rounding(min_days), self.safe_rounding(max_days), self.safe_rounding(tt_samples), locations.count(), \
            sorted(table, key=itemgetter(0, 1))


#Reminders
    def reminders_patient_events_report(self, startdate=None, enddate=None):
        if startdate:
            self.dbsr_startdate = datetime(startdate.year, startdate.month,
                                           startdate.day)
        if enddate:
            self.dbsr_enddate = \
            datetime(enddate.year, enddate.month, enddate.day)\
            + timedelta(days=1) - timedelta(seconds=0.01)
        table = []

        table.append(['  Facility', 'Count of Births'])

        cursor = connection.cursor()

        cursor.execute('SELECT locations_location.name AS Facility, count(reminders_patientevent.id) as Count ' +
                       'FROM reminders_patientevent \
                          LEFT JOIN reminders_event ON reminders_patientevent.event_id = reminders_event.id\
                          LEFT JOIN rapidsms_connection ON rapidsms_connection.id = reminders_patientevent.cba_conn_id\
                          LEFT JOIN rapidsms_contact ON rapidsms_connection.contact_id = rapidsms_contact.id\
                          LEFT JOIN locations_location  as cba_location ON rapidsms_contact.location_id = cba_location.id\
                          LEFT JOIN locations_location ON cba_location.parent_id = locations_location.id\
                          WHERE reminders_event.name = %s AND date_logged BETWEEN %s AND %s\
                          GROUP BY locations_location.name', ['Birth', self.dbsr_startdate, self.dbsr_enddate])
        total = 0
        for row in cursor.fetchall():
            total = total + row[1]
            if row[0]:
                table.append([' ' + row[0], row[1]])
            else:
                table.append([' Unknown', row[1]])
        table.append(['All listed clinics', total])
        return sorted(table, key=itemgetter(0))

#Graphing
    def get_all_dates_dictionary(self):
        """
        Returns a dictionary whose keys are all dates between startdate and
        endate
        """
        start = self.dbsr_startdate.date()
        end = self.dbsr_enddate.date()
        try:
            earliest_start = Result.objects.order_by('result_sent_date').\
            filter(notification_status='sent')[0].result_sent_date.date()
        except IndexError:
            earliest_start = None
        start = earliest_start and max(start, earliest_start) or start
        end = min(end, date.today())
        diff = (end - start).days
        if diff > self.MAX_REPORTING_PERIOD:
            return {"Sorry, I think the date range you selected is just too wide.":0}
        elif diff < 0:
            return {"Sorry, there were no DBS results received in the period you selected.":0}
        days = {}
        for i in range(diff + 1):
            days[start + timedelta(days=i)] = 0
        return days

    def dbs_graph_data(self, startdate=None, enddate=None):
        self.set_reporting_period(startdate, enddate)

        days = self.get_all_dates_dictionary()
        sent_results = self.get_results_by_status(['sent'])

        for result in sent_results:
            try:
                days[result.result_sent_date.date()] = days[result.result_sent_date.date()] + 1
            except KeyError:
                if len(days) == 1:break
        # assign some variable with a value, not so friendly to calculate in templates
        single_bar_length = max(days.values()) / self.BAR_LENGTH

        # for easy sorting, create a list of lists from the dictionary
        table = []
        for key, value in days.items():
            table.append([key, value])

        return single_bar_length, sum(days.values()), sorted(table, key=itemgetter(0, 1))

    def get_distinct_parents(self, locations, type_slugs=None):
        if not locations:
            return None
        parents = []
        for location in locations:
            if not type_slugs or (location.parent and location.parent.type.slug in type_slugs):
                parents.append(location.parent)
        return list(set(parents))

    def get_total_results_in_province(self, province):
        return Result.objects.filter(clinic__parent__parent=province).exclude(result=None).count()

    def dbs_positivity_data(self, year=None):

        def percent(num, den):
            if not num:
                return 0
            elif not den:
                return 0
            else:
                return "%4.1f" % (100.0 * num / den)

        if not year:
            year = date.today().year
        results = Result.objects.exclude(result=None)
        total_dbs = results.count()

        percent_positive_country = percent(results.filter(result__iexact='P').count(), total_dbs)
        percent_negative_country = percent(results.filter(result__iexact='N').count(), total_dbs)
        percent_rejected_country = percent(results.filter(result__in='XIR').count(), total_dbs)

        percent_positive_provinces = []
        percent_negative_provinces = []
        percent_rejected_provinces = []
        facilities = self.get_active_facilities()
        districts = self.get_distinct_parents(facilities, type_slugs=const.DISTRICT_SLUGS)
        provinces = self.get_distinct_parents(districts, type_slugs=const.PROVINCE_SLUGS)
        if provinces:
            for province in provinces:
                percent_positive_provinces.append((percent(results.filter(result__iexact='P', clinic__parent__parent=province).count(), self.get_total_results_in_province(province)), province.name))
                percent_negative_provinces.append((percent(results.filter(result__iexact='N', clinic__parent__parent=province).count(), self.get_total_results_in_province(province)), province.name))
                percent_rejected_provinces.append((percent(results.filter(result__in='XIR', clinic__parent__parent=province).count(), self.get_total_results_in_province(province)), province.name))
            
                    
        
        months_reporting = 0
        days_reporting = 0
        if results:
            start_date = results.exclude(processed_on=None).order_by('processed_on')[0].processed_on
            days_reporting = (date.today()-start_date).days
        
        year_reporting = year


        return percent_positive_country, percent_negative_country, \
            percent_rejected_country, percent_positive_provinces, \
            percent_negative_provinces, percent_rejected_provinces, \
            total_dbs, months_reporting, days_reporting, year_reporting



        days = self.get_all_dates_dictionary()
        sent_results = self.get_results_by_status(['sent'])

        for result in sent_results:
            try:
                days[result.result_sent_date.date()] = days[result.result_sent_date.date()] + 1
            except KeyError:
                if len(days) == 1:break
        # assign some variable with a value, not so friendly to calculate in templates
        single_bar_length = max(days.values()) / self.BAR_LENGTH

        # for easy sorting, create a list of lists from the dictionary
        table = []
        for key, value in days.items():
            table.append([key, value])

        return single_bar_length, sum(days.values()), sorted(table, key=itemgetter(0, 1))

