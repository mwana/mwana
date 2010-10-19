
from mwana.apps.labresults.models import Payload
import mwana.const as const
from datetime import date
from datetime import datetime
from datetime import timedelta
from django.db.models import Q
from mwana.apps.alerts.labresultsalerts.alert import Alert
from mwana.apps.alerts.models import Hub
from mwana.apps.alerts.models import Lab
from mwana.apps.labresults.models import Result
from rapidsms.contrib.locations.models import Location
from rapidsms.models import Contact

class Alerter:
    NOT_SENT_SAMPLE_MSG = "The %s district has not sent samples to "\
"%s in %s days. Please call the hub and enquire (%s) %s"
    DEFAULT_DISTICT_TRANSPORT_DAYS = 12 # days
    district_transport_days = DEFAULT_DISTICT_TRANSPORT_DAYS

    DEFAULT_CLINIC_TRANSPORT_DAYS = 12 # days
    clinic_transport_days = DEFAULT_CLINIC_TRANSPORT_DAYS

    DEFAULT_RETRIEVING_DAYS = 5 # days
    retrieving_days = DEFAULT_RETRIEVING_DAYS

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
                my_alerts.append(Alert(Alert.LAB_NOT_SENDING_PAYLOD, "%s lab "
                                 "has not sent any paylods for %s days. This "
                                 "could be a modem problem at the lab "
                                 "Please call and enquire (%s)" % (lab,
                                 (self.today - self.last_sent_payloads[lab].date()
                                 ).days, self.get_lab_number(lab))))

        return self.lab_sending_days, sorted(my_alerts)

    def get_labs_not_processing_dbs_alerts(self, days=None):
        my_alerts = []
        self.set_lab_last_processed_dbs()
        self.set_lab_processing_start(days)
        for lab in self.last_processed_dbs.keys():
            if self.last_processed_dbs[lab] < self.lab_proces_referal_date.date():
                my_alerts.append(Alert(Alert.LAB_NOT_SENDING_PAYLOD, "%s lab "
                                 "have not processed any samples for %s days. "
                                 "Please call and enquire (%s)" % (lab,
                                 (self.today-self.last_processed_dbs[lab]
                                 ).days, self.get_lab_number(lab))))

        return self.lab_processing_days, sorted(my_alerts)

    def get_clinics_not_retriving_results_alerts(self, days=None):
        self.set_retrieving_start(days)
        my_alerts = []
        clinics = Location.\
            objects.filter(
                           supportedlocation__supported=True,
                           lab_results__notification_status='notified',
                           lab_results__arrival_date__lt=self.retrieving_ref_date
                           ).distinct()
        for clinic in clinics:
            contacts = \
        Contact.active.filter(Q(location=clinic) | Q(location__parent=clinic),
                              Q(types=const.get_clinic_worker_type())).\
            order_by('pk')
            my_alerts.append(Alert(Alert.LONG_PENDING_RESULTS, "%s clinic have not"\
                             " retrieved their results. Please call and enquire "
                             "(%s)" % (clinic.name, ", ".join(contact.name + ":"
                             + contact.default_connection.identity
                             for contact in contacts))))
        return self.retrieving_days, sorted(my_alerts)

    def get_districts_not_sending_dbs_alerts(self, day=None):
        self.set_district_transport_start(day)
        self.not_sending_dbs_alerts = []
        self.set_not_sending_dbs_alerts()
        return self.district_transport_days, sorted(self.not_sending_dbs_alerts)

    def get_clinics_not_sending_dbs_alerts(self, day=None):
        my_alerts = []
        self.set_clinic_sent_dbs_start_dates(day)
        clinics = Location.objects.filter(supportedlocation__supported=True
                                          ).\
            exclude(lab_results__entered_on__gte=
                    self.clinic_trans_referal_date).\
                exclude(samplenotification__date__gte=
                        self.clinic_sent_dbs_referal_date).distinct()

        active_clinics = Location.\
            objects.filter(
                           Q(lab_results__notification_status='sent',
                           lab_results__result_sent_date__gte
                           =self.clinic_sent_dbs_referal_date),
                           Q(contact__message__text__iregex='\s*check\s*') |
                           Q(parent__contact__message__text__iregex='\s*check\s*')
                           ).distinct()
        for clinic in clinics:
            additional_text = ""
            if clinic not in active_clinics:
                additional_text = "<b>Clinic has not been using Results160 "\
                    + "during this period</b>"
                contacts = \
        Contact.active.filter(Q(location=clinic) | Q(location__parent=clinic),
                              Q(types=const.get_clinic_worker_type())).\
            order_by('pk')
                my_alerts.append(Alert(Alert.CLINIC_NOT_USING_SYSTEM, "%s clinic"
                                 "has no record of sending DBS samples in the "
                                 "last %s days. Please check "
                                 "that they have supplies by caling (%s). %s"
                                 "" % (clinic.name, self.clinic_notification_days,
                                 ", ".join(contact.name + ":"
                                 + contact.default_connection.identity
                                 for contact in contacts), additional_text)))
                             
        return self.clinic_notification_days, sorted(my_alerts)

    def set_district_last_received_dbs(self):
        results = Result.objects.exclude(entered_on=None)
        for result in results:
            district = result.clinic.parent
            if district in  self.last_received_dbs.keys():
                self.last_received_dbs[district] = \
                max(self.last_received_dbs[district], result.entered_on)
            else:
                self.last_received_dbs[district] = result.entered_on

    def set_lab_last_processed_dbs(self):
        results = Result.objects.exclude(processed_on=None)
        for result in results:
            lab = result.payload.source
            if lab in  self.last_processed_dbs.keys():
                self.last_processed_dbs[lab] = \
                max(self.last_processed_dbs[lab], result.processed_on)
            else:
                self.last_processed_dbs[lab] = result.processed_on

    def set_lab_last_sent_payload(self):
        payloads = Payload.objects.exclude(incoming_date=None)
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
        self.get_distinct_parents(self.get_facilities_for_reporting())
        for dist in all_districts:
            if dist in self.last_received_dbs.keys():
                if self.last_received_dbs[dist] < self.district_trans_referal_date.date():
                    additional = ""
                    clinics = Location.\
                    objects.filter(
                                   Q(supportedlocation__supported=True),
                                   Q(samplenotification__date__gte=
                                   self.district_trans_referal_date),
                                   Q(parent=dist) |
                                   Q(parent__parent=dist)
                                   )
                    if clinics:
                        additional = "These clinics have sent results to the"\
                        "hub: %s" % ",".join(clinic.name for clinic in clinics)
                    self.add_to_elerts(Alert.DISTRICT_NOT_SENDING_DBS,
                                       self.NOT_SENT_SAMPLE_MSG %
                                       (dist.name, self.get_hub_name(dist),
                                       (self.today-\
                                       self.last_received_dbs[dist]).days,
                                       self.get_hub_number(dist), additional))
                else:
                    pass
            else:
                self.add_to_elerts(Alert.DISTRICT_NOT_SENDING_DBS,
                                   "The %s district has never sent samples to"
                                   " %s. Please call the hub and enquire %s" %
                                   (dist.name, self.get_hub_name(dist),
                                   self.get_hub_number(dist)))

    def add_to_elerts(self, type, message):
        self.not_sending_dbs_alerts.append(Alert(type, message))
        
    def get_hub_name(self, location):
        try:
            return Hub.objects.get(district=location).name
        except Hub.DoesNotExist:
            return "(Unkown hub)"
        
    def get_hub_number(self, location):
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

    def get_facilities_for_reporting(self):
        return Location.objects.filter(supportedlocation__supported=True
                                       ).distinct()

    def get_distinct_parents(self, locations):
        if not locations:
            return None
        parents = []
        for location in locations:
            parents.append(location.parent)
        return list(set(parents))