# vim: ai ts=4 sts=4 et sw=4

from mwana.apps.websmssender.models import WebSMSLog
from mwana.apps.reports.utils.facilityfilter import user_facilities
from mwana.util import get_clinic_or_default
from rapidsms.models import Connection
from rapidsms.models import Contact
from mwana.apps.locations.models import Location
from mwana.apps.websmssender.models import StagedMessage

class SMSSender:
    def __init__(self, message, current_user=None, group=None, province=None, 
                 district=None, facility=None, worker_types=[], phone_pattern="+260"):
        self.user = current_user
        self.reporting_group = group
        self.reporting_province = province
        self.reporting_district = district
        self.reporting_facility = facility
        self.worker_types = worker_types
        self.phone_pattern = phone_pattern
        self.message = message
               

    def count_of_recipients(self):
        facs = user_facilities(current_user=self.user, group=self.reporting_group,
                               province=self.reporting_province,
                               district=self.reporting_district,
                               facility=self.reporting_facility).distinct()
        contacts = Contact.active.filter(types__in=self.worker_types,
                                         connection__identity__icontains=self.phone_pattern)
        list = []
        for contact in contacts:
            if get_clinic_or_default(contact) in facs:
                list.append(contact)
        return len(list), len(facs)

    def send_sms(self):
        facs = user_facilities(current_user=self.user, group=self.reporting_group,
                               province=self.reporting_province,
                               district=self.reporting_district,
                               facility=self.reporting_facility).distinct()
        contacts = Contact.active.filter(types__in=self.worker_types,
                                         connection__identity__icontains=self.phone_pattern)
        list = []
        for contact in contacts:
            if get_clinic_or_default(contact) in facs:
                list.append(contact)

        
        log = WebSMSLog()
        log.message = self.message
        log.recipients_count = len(list)
        log.sender = self.user.username
        log.workertype = ", ".join(type.name for type in self.worker_types)

        if self.reporting_facility:
            log.location = self.facility_name(self.reporting_facility)
        elif self.reporting_district:
            log.location = self.facility_name(self.reporting_district)
        elif self.reporting_province:
            log.location = self.facility_name(self.reporting_province)
        elif self.reporting_province:
            log.location = "All"

        log.save()

        for con in Connection.objects.filter(contact__in=list):
            StagedMessage.objects.create(connection=con, text=self.message.strip(), user=self.user.username)

        from rapidsms.contrib.httptester.utils import send_test_message
        send_test_message(identity="99999999", text="webblast %s" % self.user.username)
        return len(list)


    def facility_name(self, slug):
        return Location.objects.get(slug=slug).name