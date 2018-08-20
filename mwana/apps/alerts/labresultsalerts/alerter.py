# vim: ai ts=4 sts=4 et sw=4
from operator import itemgetter

from datetime import date
from datetime import datetime
from datetime import timedelta
from django.db import connection
from django.db.models import F
from django.db.models import Max
from django.db.models import Q
from mwana.apps.alerts.labresultsalerts.alert import Alert
from mwana.apps.alerts.models import Hub
from mwana.apps.alerts.models import Lab
from mwana.apps.labresults.models import Payload
from mwana.apps.labresults.models import Result
from mwana.apps.labresults.models import SampleNotification
from mwana.apps.locations.models import Location
from mwana.apps.reports.models import ClinicsNotSendingDBS
from mwana.apps.reports.utils.facilityfilter import get_distinct_parents
from mwana.apps.userverification.models import UserVerification
import mwana.const as const
from mwana.const import get_clinic_worker_type
from mwana.const import get_hub_worker_type
from rapidsms.contrib.messagelog.models import Message
from rapidsms.models import Contact

class Alerter:
    def __init__(self, current_user=None, group=None, province=None,
                 district=None, facility=None):
        self.today = date.today()
        self.user = current_user
        self.reporting_group = group
        self.reporting_province = province
        self.reporting_district = district
        self.reporting_facility = facility

    DEFAULT_DISTICT_TRANSPORT_DAYS = 12 # days
    district_transport_days = DEFAULT_DISTICT_TRANSPORT_DAYS

    DEFAULT_CLINIC_TRANSPORT_DAYS = 12 # days
    clinic_transport_days = DEFAULT_CLINIC_TRANSPORT_DAYS

    DEFAULT_RETRIEVING_DAYS = 5 # days
    retrieving_days = DEFAULT_RETRIEVING_DAYS

    DEFAULT_TRACING_DAYS = 14 # days
    tracing_days = DEFAULT_TRACING_DAYS

    DEFAULT_CLINIC_NOTIFICATION_DAYS = 14 # days
    clinic_notification_days = DEFAULT_CLINIC_NOTIFICATION_DAYS

    DEFAULT_LAB_PROCESSING_DAYS = 14 # days
    lab_processing_days = DEFAULT_LAB_PROCESSING_DAYS

    DEFAULT_LAB_SENDING_DAYS = 3 # days
    lab_sending_days = DEFAULT_LAB_SENDING_DAYS

    today = date.today()

    district_trans_referal_date = \
    datetime(today.year, today.month, today.day)-timedelta(days=district_transport_days)

    clinic_trans_referal_date = \
    datetime(today.year, today.month, today.day)-timedelta(days=clinic_transport_days)

    clinic_sent_dbs_referal_date = \
    datetime(today.year, today.month, today.day)-timedelta(days=clinic_notification_days)

    retrieving_ref_date = \
    datetime(today.year, today.month, today.day)-timedelta(days=retrieving_days)

    lab_proces_referal_date = \
    datetime(today.year, today.month, today.day)-timedelta(days=lab_processing_days)

    lab_send_referal_date = \
    datetime(today.year, today.month, today.day)-timedelta(days=lab_sending_days)

    last_received_dbs = {}
    last_processed_dbs = {}
    last_sent_payloads = {}
    not_sending_dbs_alerts = []

    

    def get_labs_not_sending_payloads_alerts(self, days=None):
        my_alerts = []
        self.set_lab_last_sent_payload()
        self.set_lab_sending_start(days)
        for lab in self.last_sent_payloads.keys():
            if self.last_sent_payloads[lab] < self.lab_send_referal_date:
                days_late = self.days_ago(self.last_sent_payloads[lab].date())
                level = Alert.HIGH_LEVEL if days_late >= (2 * self.lab_sending_days) else Alert.LOW_LEVEL
                my_alerts.append(Alert(Alert.LAB_NOT_SENDING_PAYLOD, "%s lab "
                                 "has not sent any DBS data for %s days. This "
                                 "could be a modem problem at the lab. "
                                 "Please call and enquire (%s)" % (lab,
                                 (self.today - self.last_sent_payloads[lab].date()
                                 ).days, self.get_lab_number(lab)),
                                 lab,
                                 days_late,
                                 -days_late,
                                 level,
                                 ""
                                 ))
        return self.lab_sending_days, sorted(my_alerts, key=itemgetter(5))

    def get_labs_not_processing_dbs_alerts(self, days=None):
        my_alerts = []
        self.set_lab_last_processed_dbs()
        self.set_lab_processing_start(days)
        for lab in self.last_processed_dbs.keys():
            if self.last_processed_dbs[lab] < self.lab_proces_referal_date.date():
                days_late = self.days_ago(self.last_processed_dbs[lab])
                level = Alert.HIGH_LEVEL if days_late >= (2 * self.lab_processing_days) else Alert.LOW_LEVEL
                my_alerts.append(Alert(Alert.LAB_NOT_SENDING_PAYLOD, "%s lab "
                                 "have not processed any samples for %s days. "
                                 "Please call and enquire (%s)" % (lab,
                                 (self.today-self.last_processed_dbs[lab]
                                 ).days, self.get_lab_number(lab)),
                                 lab,
                                 days_late,
                                 -days_late,
                                 level,
                                 ""))

        return self.lab_processing_days, sorted(my_alerts, key=itemgetter(5))

    def get_last_retrieved_results(self, location):
        try:
            return Result.objects.filter(clinic=location, result_sent_date__gt=self.tracing_ref_date).exclude(result_sent_date=None).order_by("-result_sent_date")[0].result_sent_date.date()
        except IndexError:
            return None

    def get_last_used_trace(self, location):
        try:
            return Message.objects.filter(contact__location=location, text__istartswith="trace", date__gt=self.tracing_ref_date).order_by("-date")[0].date.date()
        except:
            return date(1900, 1, 1)

    def get_clinics_not_using_trace_alerts(self, days=None):
        my_alerts = []
        self.set_tracing_start(days)

        facs = self.get_facilities_for_reporting()
        list1 = ClinicsNotSendingDBS.objects.filter(location__in=facs,
                                                    last_used_trace__gt=F('last_retrieved_results')
                                                    ).filter(last_retrieved_results__lt=self.tracing_days)

        list2 = ClinicsNotSendingDBS.objects.filter(location__in=facs,
                                                    last_used_trace=None,
                                                    ).filter(last_retrieved_results__lt=self.tracing_days)
        clinics_not_sending_dbs = (list1 | list2).distinct()
        for clinic in clinics_not_sending_dbs:

            count = Result.objects.filter(clinic=clinic.location, result_sent_date__gte=self.tracing_ref_date).count()
            level = Alert.LOW_LEVEL

            my_alerts.append(Alert(Alert.CLINIC_NOT_USING_TRACE, "%s clinic have "\
                             " retrieved %s results but have NOT used TRACE command. Please call and enquire "
                             "(%s)" % (clinic.location.name, count, clinic.contacts),
                             "%s - %s" % (clinic.location.name, clinic.location.slug),
                             clinic.last_retrieved_results,
                             -clinic.last_retrieved_results,
                             level,
                             ""
                             ))
        return self.tracing_days, sorted(my_alerts, key=itemgetter(5))

    def get_clinics_not_retriving_results_alerts(self, days=None):
        self.set_retrieving_start(days)
        my_alerts = []

        facs = self.get_facilities_for_reporting()
        clinics = facs.filter(
                              lab_results__notification_status='notified',
                              lab_results__arrival_date__lt=self.retrieving_ref_date
                              ).distinct()
        for clinic in clinics:
            contacts = \
        Contact.active.filter(location=clinic, types=const.get_clinic_worker_type()).\
            distinct().order_by('pk')
            days_late = self.days_ago(self.earliest_pending_result_arrival_date(clinic))
            level = Alert.HIGH_LEVEL if days_late >= (2 * self.retrieving_days) else Alert.LOW_LEVEL
            my_alerts.append(Alert(Alert.LONG_PENDING_RESULTS, "%s clinic have not"\
                             " retrieved their results. Please call and enquire "
                             "(%s)" % (clinic.name, ", ".join(contact.name + ":"
                             + contact.default_connection.identity
                             for contact in contacts)),
                             "%s - %s" % (clinic.name, clinic.slug),
                             days_late,
                             -days_late,
                             level,
                             ""
                             ))
        return self.retrieving_days, sorted(my_alerts, key=itemgetter(5))

    def get_districts_not_sending_dbs_alerts(self, day=None):
        self.set_district_transport_start(day)
        self.not_sending_dbs_alerts = []
        self.set_not_sending_dbs_alerts()
        return self.district_transport_days, sorted(self.not_sending_dbs_alerts, key=itemgetter(5))

    def earliest_pending_result_arrival_date(self, location):
        try:
            return Result.objects.filter(clinic=location, notification_status='notified').order_by('arrival_date')[0].arrival_date.date()
        except IndexError:
            return self.today-timedelta(days=999)

    def last_sent_samples(self, location):
        try:
            notification = SampleNotification.objects.filter(location=location).order_by('-date')[0].date.date()
        except IndexError:
            notification = date(1900, 1, 1)
        try:
            actual = Result.objects.filter(clinic=location, entered_on__lte=self.today).exclude(entered_on=None).order_by('-entered_on')[0].entered_on
        except IndexError:
            actual = date(1900, 1, 1)
        return max(notification, actual)

    def last_retrieved_or_checked(self, location):
        notification = self.last_used_sent(location)
        notification = date(1900, 1, 1)
        last_retrieved = self.last_retrieved_results(location)
        last_retrieved = date(1900, 1, 1)
        last_checked = self.last_used_check(location)
        last_checked = date(1900, 1, 1)
        last_tried_result = self.last_used_result(location)
        
        return max(notification, last_retrieved, last_checked, last_tried_result)
    
    def last_used_sent(self, location):
        try:
            return SampleNotification.objects.filter(location=location).order_by('-date')[0].date.date()
        except IndexError:
            return date(1900, 1, 1)
        
    def last_retrieved_results(self, location):
        try:
            return Result.objects.filter(clinic=location, notification_status='sent').order_by('-result_sent_date')[0].result_sent_date.date()
        except IndexError:
            return date(1900, 1, 1)
        
    
    def last_used_check(self, location):
        try:
            return Message.objects.filter(contact__location=location,
                                          direction='I',
                                          text__iregex='^check\s*'
                                          ).order_by('-date')[0].date.date()
        except IndexError:
            return date(1900, 1, 1)
        
    def last_used_result(self, location):        
        try:
            return Message.objects.filter(Q(contact__location=location),
                                          Q(direction='O'),
                                          Q(text__istartswith='The results for sample') |
                                          Q(text__istartswith='There are currently no results')).order_by('-date')[0].date.date()
        except IndexError:
            return date(1900, 1, 1)

    def _last_used_result(self, location, messages):
        try:
            return messages.filter(contact__location=location).order_by('-date')[0].date.date()
        except IndexError:
            return date(1900, 1, 1)

    def days_ago(self, p_date):
        return (self.today - p_date).days
        
    def get_clinics_not_sending_dbs_alerts(self, day=None):
        my_alerts = []
        self.set_clinic_sent_dbs_start_dates(day)
        facs = self.get_facilities_for_reporting()
        clinics = facs.\
            exclude(lab_results__entered_on__gte=
                    self.clinic_sent_dbs_referal_date.date()).\
                exclude(samplenotification__date__gte=
                        self.clinic_sent_dbs_referal_date.date()).distinct()

        sites = ClinicsNotSendingDBS.objects.filter(location__in=clinics).order_by('location__name')
        for clinic in sites:
            additional_text = ""

            # @type clinic ClinicsNotSendingDBS
            if clinic.last_retrieved_results is not None:
                additional_text += "This clinic last retrieved results "\
                + "%s days ago" % clinic.last_retrieved_results
            else:
                additional_text += "This clinic has never retrieved results"

            if clinic.last_used_sent is not None:
                additional_text += ", last used SENT keyword "\
                + "%s days ago" % clinic.last_used_sent
            else:
                additional_text += ", has never used SENT keyword"

            if clinic.last_used_check is not None:
                additional_text += ", last used CHECK keyword "\
                + "%s days ago" % clinic.last_used_check
            else:
                additional_text += ", has never CHECKed for results"

            if clinic.last_used_result is not None:
                additional_text += ", last used RESULT keyword "\
                + "%s days ago." % clinic.last_used_result
            else:
                additional_text += ", has never used RESULT keyword."
           
            level = Alert.HIGH_LEVEL if (clinic.last_sent_samples is None or clinic.last_sent_samples >= (2 * self.clinic_notification_days)) else Alert.LOW_LEVEL
            alert_msg = ("Clinic "
                         "has no record of sending DBS samples in  the last"
                         " %s days. Please check "
                         "that they have supplies by calling (%s)."
                         "" % (clinic.last_sent_samples,
                         clinic.contacts))
            if clinic.last_sent_samples is None:
                alert_msg = ("Clinic has no record of sending DBS samples "
                             "since it was added to the SMS system. "
                             "Please check that they have supplies by calling (%s)."
                             "" % clinic.contacts)
            my_alerts.append(Alert(Alert.CLINIC_NOT_USING_SYSTEM,
                             alert_msg,
                             "%s - %s" % (clinic.location.name, clinic.location.slug),
                             clinic.last_sent_samples or 40001,
                             -(clinic.last_sent_samples or 40001),
                             level,
                             additional_text
                             ))

        return self.clinic_notification_days, sorted(my_alerts, key=itemgetter(5))

    def set_district_last_received_dbs(self):
        # uses raw sql for performance reasons
        ids = self._get_reporting_ids()
        district_ids = self._get_district_reporting_ids()
        
        sql = '''
            SELECT id, max(entered_on) FROM(
            SELECT district.id, max(entered_on) as entered_on FROM labresults_result
            join locations_location as clinic on clinic.id = labresults_result.clinic_id
            join locations_location as district on district.id = clinic.parent_id
            WHERE entered_on is not null
            and clinic_id in (''' + ids + ''')
            GROUP BY district.id

            UNION ALL

            SELECT district.id, max(date)::date as entered_on FROM hub_workflow_hubsamplenotification
            join locations_location as clinic on clinic.id = hub_workflow_hubsamplenotification.lab_id
            join locations_location as district on district.id = clinic.parent_id
            and district.id in (''' + district_ids + ''')
            GROUP BY district.id
            ) a
            GROUP BY id;
       '''
        cursor = connection.cursor()
        cursor.execute(sql)

        rows = cursor.fetchall()

        for row in rows:
            self.last_received_dbs[row[0]] = row[1]

    def set_lab_last_processed_dbs(self):

        # uses raw sql for performance reasons
        ids = self._get_reporting_ids()

        sql1 = '''
        SELECT DISTINCT "source" FROM labresults_result
        JOIN labresults_payload on labresults_payload.id=labresults_result.payload_id
        WHERE clinic_id in (''' + ids + ''');
        '''
        
        cursor1 = connection.cursor()
        cursor1.execute(sql1)
        rows1 = cursor1.fetchall()
        sources = [x[0] for x in rows1]

        sql = '''
        SELECT "source", max(processed_on) FROM labresults_result
        JOIN labresults_payload on labresults_payload.id=labresults_result.payload_id
        WHERE processed_on IS NOT null
        GROUP BY "source";
        '''
        cursor = connection.cursor()
        cursor.execute(sql)

        rows = cursor.fetchall()
        self.last_processed_dbs.clear()
        for row in rows:
            source = row[0]
            if source in sources:
                self.last_processed_dbs[source] = row[1]

        sql2 = '''
        SELECT source_key, max(processed_on)  FROM labresults_result
        join alerts_lab on substring(sample_id, 1, 3) = lab_code
        WHERE processed_on IS NOT null
        GROUP BY source_key;
        '''
        cursor = connection.cursor()
        cursor.execute(sql2)
        rows = cursor.fetchall()
        for row in rows:
            source = row[0]
            if source in sources:
                if self.last_processed_dbs[source] < row[1]:
                    self.last_processed_dbs[source] = row[1]
                elif not self.last_processed_dbs[source]:
                    self.last_processed_dbs[source] = row[1]
      
    def set_lab_last_sent_payload(self):
        self.last_sent_payloads = dict(Payload.objects.all().values_list("source").annotate(Max('incoming_date')))

    def set_not_sending_dbs_alerts(self):
        self.set_district_last_received_dbs()
        
        all_districts = \
        get_distinct_parents(self.get_facilities_for_reporting())
        for dist in all_districts:
            if dist.id in self.last_received_dbs.keys():
                if self.last_received_dbs[dist.id] < self.district_trans_referal_date.date():
                    additional = ""
                    clinics = Location.\
                    objects.filter(
                                   Q(supportedlocation__supported=True),
                                   Q(samplenotification__date__gte=
                                   self.district_trans_referal_date.date()),
                                   Q(parent=dist) |
                                   Q(parent__parent=dist)
                                   ).distinct()
                    if clinics:
                        additional = "These clinics have sent samples to the "\
                        "hub: %s" % ",".join(clinic.name for clinic in clinics)
                    days_late = (self.today - self.last_received_dbs[dist.id]).days
                    level = Alert.HIGH_LEVEL if days_late >= (2 * self.district_transport_days) else Alert.LOW_LEVEL
                    self.add_to_district_dbs_elerts(Alert.DISTRICT_NOT_SENDING_DBS,
                                                    "The %s district hub (%s) has not "
                                                    "sent samples to %s in %s "
                                                    "days. Please call the hub "
                                                    "and enquire (%s)" %
                                                    (dist.name,
                                                    self.get_hub_name(dist),
                                                    self.get_lab_name(dist),
                                                    (self.today-\
                                                    self.last_received_dbs[dist.id]).days,
                                                    self.get_hub_number(dist)),
                                                    dist.name,
                                                    days_late,
                                                    -days_late,
                                                    level,
                                                    additional
                                                    )
                else:
                    pass
            else:
                self.add_to_district_dbs_elerts(Alert.DISTRICT_NOT_SENDING_DBS,
                                                "The %s district hub (%s) has never sent samples to"
                                                " %s. Please call the hub and enquire (%s)" %
                                                (dist.name, self.get_hub_name(dist),
                                                self.get_lab_name(dist),
                                                self.get_hub_number(dist)),
                                                dist.name,
                                                999,
                                                -999,
                                                Alert.HIGH_LEVEL,
                                                "")
    def last_used_system(self, contact):
        latest = Message.objects.filter(
                                        contact=contact,
                                        direction='I',
                                        ).aggregate(date=Max('date'))
        if latest['date']:
            return (datetime.today() - latest['date']).days
        else:
            return None


    def get_complying_contacts(self):
        
        #TODO: to better implementation of fix
        days_back = 75
        today = datetime.today()
        date_back = datetime(today.year, today.month, today.day) - timedelta(days=days_back)


        supported_contacts = Contact.active.filter(types=get_clinic_worker_type(),
                                                   location__supportedlocation__supported=True).distinct()

        return supported_contacts.filter(message__direction="I", message__date__gte=date_back).distinct()


    def get_inactive_workers_alerts(self):
        facilities = (self.get_facilities_for_reporting())
        inactive_alerts = []
        complying_contacts = self.get_complying_contacts()
        
        defaulters = UserVerification.objects.\
            filter(responded=False, contact__is_active=True,
                   contact__types=get_clinic_worker_type(), facility__in=facilities).distinct()
       
        defaulters = [item for item in defaulters.exclude(contact__in=complying_contacts)]
        
        def_facs = set(defa.facility for defa in defaulters)
        
        for facility in def_facs:
            days_late = 75
            fac_defaulters = filter(lambda x: x.facility == facility, defaulters)
            if not fac_defaulters:
                continue
            msg = ("The following staff registered at %s have not been using "
                   "Results160 for too long and have been unresponsive. "
                   "The last time they used the system is "
                   "as shown. Please call and enquire. " % (facility.name))

            contacts  = []
            temp = []
            for defaulter in fac_defaulters:
                contacts.append(defaulter.contact)
            for contact in set(contacts):
                last_used = self.last_used_system(contact)
                last_used_msg = "%s days ago" % last_used if last_used else "Never"
                temp.append("%s (%s) %s" % (contact.name,
                            contact.default_connection.identity, last_used_msg
                            ))
                if last_used: days_late = max(days_late, last_used)

            msg = msg + "; ".join(msg for msg in temp) + "."

            inactive_alerts.append(Alert(Alert.WORKER_NOT_USING_SYSTEM, msg,
            "%s - %s" % (defaulter.facility.name, defaulter.facility.slug),
                                   days_late, -days_late, Alert.HIGH_LEVEL, ""))
        return sorted(inactive_alerts, key=itemgetter(5))


    def add_to_district_dbs_elerts(self, type, message, culprit=None, days_late=None, sort_field=None, level=None, extra=None):
        self.not_sending_dbs_alerts.append(Alert(type, message, culprit,
                                           days_late, sort_field, level, extra))

    def get_hub_name(self, district):
        try:
            return Hub.objects.get(district=district).name
        except Hub.DoesNotExist:
            return ','.join(loc.name for loc in Location.objects.filter(contact__types=get_hub_worker_type(), parent=district).distinct()) or "Unkown hub"
                
    def get_hub_number(self, location):
        pipo = Contact.active.filter(types=get_hub_worker_type(), location__parent=location)
        if pipo:
            return ", ".join(c.name + ": " + c.default_connection.identity for c in pipo)
        try:
            return Hub.objects.exclude(Q(phone=None) | Q(phone='')).\
        get(district=location).phone
        except Hub.DoesNotExist:
            return "Unkown number"

    def get_lab_number(self, lab):
        try:
            return Lab.objects.exclude(Q(phone=None) | Q(phone='')).\
        get(source_key=lab).phone
        except Lab.DoesNotExist:
            return "(Unkown number)"

    def get_lab_name(self, district):
        try:
            return Payload.objects.filter(lab_results__clinic__parent\
                                          =district)[0].source
        except:
            return "(Unkown lab)"

    def set_clinic_sent_dbs_start_dates(self, days):
        if days:
            self.clinic_notification_days = days
        else:
            self.clinic_notification_days = self.DEFAULT_CLINIC_NOTIFICATION_DAYS
        self.clinic_sent_dbs_referal_date = \
        datetime(self.today.year, self.today.month,
                 self.today.day)-timedelta(days=self.clinic_notification_days-1)

    def set_district_transport_start(self, days):
        if days:
            self.district_transport_days = days
        else:
            self.district_transport_days = self.DEFAULT_DISTICT_TRANSPORT_DAYS
        self.district_trans_referal_date = \
        datetime(self.today.year, self.today.month,
                 self.today.day)-timedelta(days=self.district_transport_days-1)

    def set_lab_processing_start(self, days):
        if days:
            self.lab_processing_days = days
        else:
            self.lab_processing_days = self.DEFAULT_LAB_PROCESSING_DAYS
        self.lab_proces_referal_date = \
        datetime(self.today.year, self.today.month,
                 self.today.day)-timedelta(days=self.lab_processing_days-1)

    def set_lab_sending_start(self, days):
        if days:
            self.lab_sending_days = days
        else:
            self.lab_sending_days = self.DEFAULT_LAB_SENDING_DAYS
        self.lab_send_referal_date = \
        datetime(self.today.year, self.today.month,
                 self.today.day)-timedelta(days=self.lab_sending_days-1)

    def set_clinic_transport_start(self, days):
        if days:
            self.district_transport_days = days
        else:
            self.district_transport_days = self.DEFAULT_DISTICT_TRANSPORT_DAYS
        self.district_trans_referal_date = \
        datetime(self.today.year, self.today.month,
                 self.today.day)-timedelta(days=self.district_transport_days-1)

    def set_retrieving_start(self, days):
        if days:
            self.retrieving_days = days
        else:
            self.retrieving_days = self.DEFAULT_RETRIEVING_DAYS
        self.retrieving_ref_date = \
        datetime(self.today.year, self.today.month,
                 self.today.day)-timedelta(days=self.retrieving_days-1)

    def set_tracing_start(self, days):
        if days:
            self.tracing_days = days
        else:
            self.tracing_days = self.DEFAULT_TRACING_DAYS
        self.tracing_ref_date = \
        datetime(self.today.year, self.today.month,
                 self.today.day)-timedelta(days=self.tracing_days-1)

    def get_facilities_for_reporting(self):
        facs = Location.objects.filter(supportedlocation__supported=True, groupfacilitymapping__group__groupusermapping__user=self.user)
        if self.reporting_group:
            facs = facs.filter(Q(groupfacilitymapping__group__id=self.reporting_group)
                               | Q(groupfacilitymapping__group__name__iexact=self.reporting_group))
        if self.reporting_facility:
            facs = facs.filter(slug=self.reporting_facility)
        elif self.reporting_district:
            facs = facs.filter(parent__slug=self.reporting_district)
        elif self.reporting_province:
            facs = facs.filter(parent__parent__slug=self.reporting_province)
        return facs.filter(supportedlocation__supported=True
                           ).distinct()

    def my_payload_sources(self):
        facs = self.get_facilities_for_reporting()
        payloads = Payload.objects.filter(lab_results__clinic__in=facs)
        if payloads:
            return [payloads[0].source]
        return []

    def _get_reporting_ids(self):
        ids = ", ".join("%s" % fac.id for fac in self.get_facilities_for_reporting())
        if not ids:
            ids = '-1'
            
        return ids

    def _get_district_reporting_ids(self):
        ids = ", ".join("%s" % loc.id for loc in get_distinct_parents(self.get_facilities_for_reporting()))
        if not ids:
            ids = '-1'

        return ids