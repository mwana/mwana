from datetime import date
from datetime import datetime
from datetime import timedelta

from django.db.models import Count
from django.db.models import Q
from django.db.models import Sum
from mwana.apps.labresults.models import Payload
from mwana.apps.labresults.models import Result
from mwana.apps.labresults.models import SampleNotification
from rapidsms.contrib.locations.models import Location
from django.db import connection
from operator import itemgetter

class Results160Reports:
    STATUS_CHOICES = ('in-transit', 'unprocessed', 'new', 'notified', 'sent', 'updated')
    today = date.today()
    dbsr_enddate = datetime(today.year, today.month, today.day) + timedelta(days=1)
    -timedelta(seconds=0.01)
    dbsr_startdate = datetime(today.year, today.month, today.day)-timedelta(days=30)


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
        return Location.objects.filter(Q(lab_results__notification_status__in=['sent']),
                                       Q(samplenotification__date__gt=self.dbsr_startdate)
                                       | Q(samplenotification__date=self.dbsr_startdate),
                                       Q(samplenotification__date__lt=self.dbsr_enddate) |
                                       Q(samplenotification__date=self.dbsr_enddate)
                                       ).distinct()

    def get_facilities_for_rsts_reporting(self):
        return Location.objects.filter(Q(lab_results__notification_status__in=['sent']),
                                       Q(lab_results__result_sent_date__gt=self.dbsr_startdate)
                                       | Q(lab_results__result_sent_date=self.dbsr_startdate),
                                       Q(lab_results__result_sent_date__lt=self.dbsr_enddate) |
                                       Q(lab_results__result_sent_date=self.dbsr_enddate)
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


    def get_results_for_reporting(self):
        """Returns results query set in reporting period"""
        return Result.objects.filter(Q(result_sent_date__gt=self.dbsr_startdate)
                                     | Q(result_sent_date=self.dbsr_startdate),
                                     Q(result_sent_date__lt=self.dbsr_enddate) |
                                     Q(result_sent_date=self.dbsr_enddate))

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
            table.append([' '+ row[0], row[1]])
        table.append(['All listed sources',total])
        return sorted(table,  key=lambda table: table[0].lower())

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

            table.append([' ' + location.parent.name, ' ' + location.name, \
                         new, notified, updated, unprocessed, total])
            tt_new = tt_new + new
            tt_notified = tt_notified + notified
            tt_updated = tt_updated + updated
            tt_unprocessed = tt_unprocessed + unprocessed
            tt_total = tt_total + total
            
        table.append(['All listed districts', 'All listed  clinics', tt_new, tt_notified, tt_updated, tt_unprocessed, tt_total])
        return sorted(table, key=itemgetter(0,1))

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
        return sorted(table, key=itemgetter(0,1))

    def dbs_samples_at_lab_report(self, startdate=None, enddate=None):
        self.set_reporting_period(startdate, enddate)
        table = []

        table.append(['  District', '  Facility', 'Samples'])

        received = 0
        tt_received = 0
        for location in self.get_facilities_for_samples_at_lab():
            received = self.get_results_by_status_and_location(self.STATUS_CHOICES, location).count()
            tt_received = tt_received + received

            table.append([' ' + location.parent.name, ' ' + location.name, received,])
        table.append(['All listed districts', 'All listed  clinics', tt_received])
        return sorted(table, key=itemgetter(0,1))

    def dbs_sent_results_report(self, startdate=None, enddate=None):
        self.set_reporting_period(startdate, enddate)
        table = []

        table.append(['  District', '  Facility',
                     'Positive', 'Negative', 'Rejected', 'Total Sent'])
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
        return sorted(table, key=itemgetter(0,1))


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
                          GROUP BY reminders_event.name, locations_location.name', ['Birth',self.dbsr_startdate, self.dbsr_enddate])
        total = 0
        for row in cursor.fetchall():
            total = total + row[1]
            table.append([' '+ row[0], row[1]])
        table.append(['All listed clinics',total])
        return sorted(table, key=itemgetter(0))

