# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.reports.utils.facilityfilter import get_distinct_parents
from mwana.apps.userverification.models import UserVerification
from django.db.models import Max

from operator import itemgetter

import mwana.const as const
from datetime import date
from datetime import datetime
from datetime import timedelta
from django.db.models import Q
from mwana.apps.alerts.labresultsalerts.alert import Alert
from mwana.apps.alerts.models import Hub
from mwana.apps.alerts.models import Lab
from mwana.apps.labresults.models import Payload
from mwana.apps.labresults.models import Result
from mwana.apps.labresults.models import SampleNotification
from mwana.apps.locations.models import Location
from rapidsms.contrib.messagelog.models import Message
from rapidsms.models import Contact
from mwana.const import get_hub_worker_type
from mwana.const import get_clinic_worker_type

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
        
        for clinic in facs:
            last_retrieved_results = self.get_last_retrieved_results(clinic)
            last_used_trace = self.get_last_used_trace(clinic)

            if last_retrieved_results is None:
                continue

            if last_retrieved_results <= last_used_trace:
                continue
            count = Result.objects.filter(clinic=clinic, result_sent_date__gte=self.tracing_ref_date).count()
            days_late = self.days_ago(last_retrieved_results)
            level = Alert.LOW_LEVEL
            contacts = \
        Contact.active.filter(location=clinic, types=const.get_clinic_worker_type()).\
            distinct().order_by('pk')
            my_alerts.append(Alert(Alert.CLINIC_NOT_USING_TRACE, "%s clinic have "\
                             " retrieved %s results but have NOT used TRACE command. Please call and enquire "
                             "(%s)" % (clinic.name, count, ", ".join(contact.name + ":"
                             + contact.default_connection.identity
                             for contact in contacts)),
                             clinic.name,
                             days_late,
                             -days_late,
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
                             clinic.name,
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
            actual = Result.objects.filter(clinic=location).exclude(entered_on=None).order_by('-entered_on')[0].entered_on
        except IndexError:
            actual = date(1900, 1, 1)
        return max(notification, actual)

    def last_retrieved_or_checked(self, location):
        notification = self.last_used_sent(location)
        notification = date(1900, 1, 1)
        last_retreived = self.last_retreived_results(location)
        last_retreived = date(1900, 1, 1)
        last_checked = self.last_used_check(location)
        last_checked = date(1900, 1, 1)
        last_tried_result = self.last_used_result(location)
        
        return max(notification, last_retreived, last_checked, last_tried_result)
    
    def last_used_sent(self, location):
        try:
            return SampleNotification.objects.filter(location=location).order_by('-date')[0].date.date()
        except IndexError:
            return date(1900, 1, 1)
        
    def last_retreived_results(self, location):
        try:
            return Result.objects.filter(clinic=location, notification_status='sent').order_by('-result_sent_date')[0].result_sent_date.date()
        except IndexError:
            return date(1900, 1, 1)
        
    
    def last_used_check(self, location):
        try:
            return Message.objects.filter(contact__location=location ,
                                                  direction='I',
                                                  text__iregex='^check\s*'
                                                  ).order_by('-date')[0].date.date()
        except IndexError:
            return date(1900, 1, 1)
        
    def last_used_result(self, location):        
        try:
            return Message.objects.filter(Q(contact__location=location) ,
                                          Q(direction='O'),
                                          Q(text__istartswith='The'),
                                           Q(text__istartswith='The results for sample') |
                                           Q(text__istartswith='There are currently no results')).order_by('-date')[0].date.date()
        except IndexError:
            return date(1900, 1, 1)

    def days_ago(self, date):
        return (self.today - date).days
    
    
        
    def get_clinics_not_sending_dbs_alerts(self, day=None):
        my_alerts = []
        self.set_clinic_sent_dbs_start_dates(day)
        facs = self.get_facilities_for_reporting()
        clinics = facs.\
            exclude(lab_results__entered_on__gte=
                    self.clinic_sent_dbs_referal_date.date()).\
                exclude(samplenotification__date__gte=
                        self.clinic_sent_dbs_referal_date.date()).distinct()
        
        for clinic in clinics:
            additional_text = ""
            days_ago = self.days_ago(self.last_retreived_results(clinic))
            if days_ago < 40000:
                additional_text += "This clinic last retrieved results "\
                + "%s days ago" % days_ago
            else:
                additional_text += "This clinic has never retrieved results"
                
            days_ago = self.days_ago(self.last_used_sent(clinic))
            if days_ago < 40000:
                additional_text += ", last used SENT keyword "\
                + "%s days ago" % days_ago
            else:
                additional_text += ", has never used SENT keyword"
                
            days_ago = self.days_ago(self.last_used_check(clinic))
            if days_ago < 40000:
                additional_text += ", last used CHECK keyword "\
                + "%s days ago" % days_ago
            else:
                additional_text += ", has never CHECKed for results"
                         
            days_ago = self.days_ago(self.last_used_result(clinic))
            if days_ago < 40000:
                additional_text += ", last used RESULT keyword "\
                + "%s days ago." % days_ago
            else:
                additional_text += ", has never used RESULT keyword."
                
                
            contacts = \
    Contact.active.filter(location=clinic,types=const.get_clinic_worker_type()).\
        distinct().order_by('name')
            days_late = self.days_ago(self.last_sent_samples(clinic))
            level = Alert.HIGH_LEVEL if days_late >= (2 * self.clinic_notification_days) else Alert.LOW_LEVEL
            alert_msg = ("Clinic "
                             "has no record of sending DBS samples in  the last"
                             " %s days. Please check "
                             "that they have supplies by calling (%s)."
                             "" % (days_late,
                             ", ".join(contact.name + ":"
                             + contact.default_connection.identity
                             for contact in contacts)))
            if days_late > 40000:
                alert_msg = ("Clinic has no record of sending DBS samples "
                             "since it was added to the SMS system. "
                             "Please check that they have supplies by calling (%s)."
                             "" % ( ", ".join(contact.name + ":"
                             + contact.default_connection.identity
                             for contact in contacts)))
            my_alerts.append(Alert(Alert.CLINIC_NOT_USING_SYSTEM,
                             alert_msg,
                             clinic.name,
                             days_late,
                             -days_late,
                             level,
                             additional_text
                             ))

        return self.clinic_notification_days, sorted(my_alerts, key=itemgetter(5))

    def set_district_last_received_dbs(self):
        results = Result.objects.exclude(entered_on=None).exclude(clinic=None)
        for result in results:
            district = result.clinic.parent
            if district in  self.last_received_dbs.keys():
                self.last_received_dbs[district] = \
                max(self.last_received_dbs[district], result.entered_on)
            else:
                self.last_received_dbs[district] = result.entered_on

    def set_lab_last_processed_dbs(self):
        results = Result.objects.exclude(processed_on=None).\
        filter(clinic__in=self.get_facilities_for_reporting())
        self.last_processed_dbs.clear()
        for result in results:
            lab = result.payload.source
            if lab in  self.last_processed_dbs.keys():
                self.last_processed_dbs[lab] = \
                max(self.last_processed_dbs[lab], result.processed_on)
            else:
                self.last_processed_dbs[lab] = result.processed_on

    def set_lab_last_sent_payload(self):
        payloads = Payload.objects.exclude(incoming_date=None).\
        filter(source__in=self.my_payload_sources())
        self.last_sent_payloads.clear()
        for payload in payloads:
            lab = payload.source
            if lab in  self.last_sent_payloads.keys():
                self.last_sent_payloads[lab] = \
                max(self.last_sent_payloads[lab], payload.incoming_date)
            else:
                self.last_sent_payloads[lab] = payload.incoming_date


    def set_not_sending_dbs_alerts(self):
        self.set_district_last_received_dbs()

        all_districts = \
        get_distinct_parents(self.get_facilities_for_reporting())
        for dist in all_districts:
            if dist in self.last_received_dbs.keys():
                if self.last_received_dbs[dist] < self.district_trans_referal_date.date():
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
                    days_late = (self.today - self.last_received_dbs[dist]).days
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
                                                    self.last_received_dbs[dist]).days,
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
        
        for facility in facilities:
            days_late = 75
            defaulters = UserVerification.objects.exclude(responded="True").\
            filter(facility=facility, contact__is_active=True).distinct()

            defaulters = defaulters.exclude(contact__in=self.get_complying_contacts())

            if not defaulters:
                continue

            msg = ("The following staff registered at %s have not been using "
             "Results160 for too long and have been unresponsive. "
             "The last time they used the system is "
            "as shown. Please call and enquire. " % (facility.name))

            contacts  = []
            temp = []
            for defaulter in defaulters:
                contacts.append(defaulter.contact)
            for contact in set(contacts):
                last_used = self.last_used_system(contact)
                last_used_msg = "%s days ago" % last_used if last_used else "Never"
                temp.append("%s (%s) %s" % (contact.name,
                contact.default_connection.identity, last_used_msg
                ))
                if last_used: days_late = max(days_late, last_used)

            msg = msg + "; ".join(msg for msg in temp) + "."

            inactive_alerts.append(Alert(Alert.WORKER_NOT_USING_SYSTEM, msg, defaulter.facility.name,
            days_late, -days_late, Alert.HIGH_LEVEL, ""))
        return sorted(inactive_alerts, key=itemgetter(5))


    def add_to_district_dbs_elerts(self, type, message, culprit=None, days_late=None, sort_field=None, level=None, extra=None):
        self.not_sending_dbs_alerts.append(Alert(type, message, culprit,
                                           days_late, sort_field, level, extra))

    def get_hub_name(self, location):
        try:
            return Location.objects.filter(contact__types=get_hub_worker_type()).distinct().get(parent=location).name
        except:
            try:
                return Hub.objects.get(district=location).name
            except Hub.DoesNotExist:
                return "(Unkown hub)"

    def get_hub_number(self, location):
        pipo=Contact.active.filter(types=get_hub_worker_type(),location__parent=location)
        if pipo:
            return ", ".join(c.name+": "+c.default_connection.identity for c in pipo)
        try:
            return Hub.objects.exclude(Q(phone=None) | Q(phone='')).\
        get(district=location).phone
        except Hub.DoesNotExist:
            return "(Unkown number)"

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
            facs= facs.filter(Q(groupfacilitymapping__group__id=self.reporting_group)
            |Q(groupfacilitymapping__group__name__iexact=self.reporting_group))
        if self.reporting_facility:
            facs = facs.filter(slug=self.reporting_facility)
        # TODO : use location.parent instead of relying on slug naming convetions
        elif self.reporting_district:
            facs = facs.filter(slug__startswith=self.reporting_district[:4])
        elif self.reporting_province:
            facs = facs.filter(slug__startswith=self.reporting_province[:2])
        return facs.filter(supportedlocation__supported=True
                                       ).distinct()

    def my_payload_sources(self):
        facs = self.get_facilities_for_reporting()
        payloads = Payload.objects.filter(lab_results__clinic__in=facs)
        if payloads:
            return [payloads[0].source]
        return []
  