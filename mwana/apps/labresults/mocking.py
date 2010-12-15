# vim: ai ts=4 sts=4 et sw=4
import datetime
import mwana.const as const
import random
from datetime import date
from datetime import timedelta
from django.conf import settings
from mwana.apps.hub_workflow.tasks import get_lab_name, DBS_SUMMARY
from mwana.apps.hub_workflow.tasks import SAMPLES_RECEIVED_TODAY
from mwana.apps.labresults.messages import ALREADY_COLLECTED
from mwana.apps.labresults.messages import BAD_PIN
from mwana.apps.labresults.messages import DEMO_FAIL
from mwana.apps.labresults.messages import HUB_DEMO_FAIL
from mwana.apps.labresults.messages import INSTRUCTIONS
from mwana.apps.labresults.messages import RESULTS_PROCESSED
from mwana.apps.labresults.messages import RESULTS_READY
from mwana.apps.labresults.messages import SELF_COLLECTED
from mwana.apps.labresults.messages import build_results_messages
from mwana.apps.labresults.models import Result
from mwana.apps.labresults.util import is_eligible_for_results
from mwana.apps.locations.models import Location
from mwana.const import get_district_worker_type
from mwana.const import get_hub_worker_type
from mwana.const import get_province_worker_type
from rapidsms.log.mixin import LoggerMixin
from rapidsms.messages.outgoing import OutgoingMessage
from rapidsms.models import Contact


class MockResultUtility(LoggerMixin):
    """
    A mock data utility.  This allows you to script some demo/testing scripts
    while not reading or writing any results data to the database.
    """
    
    waiting_for_pin = {}
    last_collectors = {}
    
    def handle(self, message):
        if message.text.strip().upper().startswith("DEMO"):
            rest = message.text.strip()[4:].strip()
            clinic = None
            if rest:
                # optionally allow the tester to pass in a clinic code
                try:
                    clinic = Location.objects.get(slug__iexact=rest)
                except Location.DoesNotExist:
                    # maybe they just passed along some extra text
                    pass 
            if not clinic and message.connection.contact \
                and message.connection.contact.location:
                    # They were already registered for a particular clinic
                    # so assume they want to use that one.
                    clinic = message.connection.contact.location
            if not clinic:
                message.respond(DEMO_FAIL)
            else:
                # Fake like we need to prompt their clinic for results, as a means
                # to conduct user testing.  The mocker does not touch the database
                self.info("Initiating a demo sequence to clinic: %s" % clinic)
                self.fake_pending_results(clinic)
            return True
        elif message.connection in self.waiting_for_pin \
            and message.connection.contact:
                pin = message.text.strip()
                if pin.upper() == message.connection.contact.pin.upper():
                    results = self.waiting_for_pin[message.connection]
                    responses = build_results_messages(results)
            
                    for resp in responses:
                        message.respond(resp)
                
                    message.respond(INSTRUCTIONS, name=message.connection.contact.name)
                
                    self.waiting_for_pin.pop(message.connection)
                
                    # remove pending contacts for this clinic and notify them it
                    # was taken care of
                    clinic_connections = [contact.default_connection for contact in \
                        Contact.active.filter\
                        (location=message.connection.contact.location)]
                
                    for conn in clinic_connections:
                        if conn in self.waiting_for_pin:
                            self.waiting_for_pin.pop(conn)
                            OutgoingMessage(conn, RESULTS_PROCESSED,
                                            name=message.connection.contact.name).send()
                
                    self.last_collectors[message.connection.contact.location] = message.connection.contact
                    return True
                else:
                    # pass a secret message to default phase, see app.py
                    self.debug("caught a potential bad pin: %s for %s" % \
                               (message.text, message.connection))
                    message.possible_bad_mock_pin = True

        
    def default(self, message):
        if hasattr(message, "possible_bad_mock_pin"):
            message.respond(BAD_PIN)                
            return True
        elif is_eligible_for_results(message.connection) \
            and message.connection.contact.location in self.last_collectors \
            and message.text.strip().upper() == message.connection.contact.pin.upper():
                if message.connection.contact == self.last_collectors[message.connection.contact.location]:
                    message.respond(SELF_COLLECTED, name=message.connection.contact.name)
                else:
                    message.respond(ALREADY_COLLECTED, name=message.connection.contact.name,
                                    collector=self.last_collectors[message.connection.contact.location])
                return True

    def fake_pending_results(self, clinic):
        """Notifies clinic staff that results are ready via sms, except
           this is fake!"""
        contacts = Contact.active.filter(types=const.get_clinic_worker_type()).location(clinic)
        results = get_fake_results(3, clinic)
        for contact in contacts:
            msg = OutgoingMessage(connection=contact.default_connection, 
                                  template=RESULTS_READY,
                                  name=contact.name, count=len(results))
            msg.send()
            self._mark_results_pending(results, msg.connection)
    
    
    def _mark_results_pending(self, results, connection):
        self.waiting_for_pin[connection] = results
        
    
def get_fake_results(count, clinic, starting_requisition_id=9990,
                     requisition_id_format=None,
                     notification_status_choices=("new", )):
    """
    Fake results for demos and trainings. Defaults to a high requisition_id
    that is not likely to be found at the clinic.
    """
    results = []
    if requisition_id_format is None:
        requisition_id_format = getattr(settings, "RESULTS160_FAKE_ID_FORMAT",
                                        "{id:04d}")
    current_requisition_id = starting_requisition_id
    # strip off indeterminate/inconsistent, as those results won't be sent
    result_choices = [r[0] for r in Result.RESULT_CHOICES[:3]]
    if clinic.type.slug in const.ZONE_SLUGS:
        clinic = clinic.parent
    for i in range(count):
        requisition_id = requisition_id_format.format(id=(current_requisition_id + i),
                                                      clinic=clinic.slug)
        status = random.choice(notification_status_choices)
        result = Result(requisition_id=requisition_id, clinic=clinic,
                        # make sure we get at least one of each possible result
                        result=result_choices[i % len(result_choices)],
                        collected_on=datetime.datetime.today(),
                        entered_on=datetime.datetime.today(),
                        notification_status=status)
        results.append(result)
    return results

class MockSMSReportsUtility(LoggerMixin):
    """
    A mock reports utility.  This allows you to do some demo/training scripts
    while not reading or writing any results data to the database.
    """

    def handle(self, message):
        if message.text.strip().upper().startswith("HUBDEMO"):
            rest = message.text.strip()[7:].strip()
            clinic = self.get_clinic(message, rest)

            if not clinic:
                message.respond(HUB_DEMO_FAIL)
            else:
                # Fake like we need to prompt their clinic for results, as a means
                # to conduct user testing.  The mocker does not touch the database
                self.info("Initiating demo reports to clinic: %s" % clinic)
                self.fake_send_dbs_recvd_at_lab_notification(clinic)
                self.fake_sending_hub_reports(clinic)
            return True
        elif message.text.strip().upper().startswith("DHODEMO"):
            rest = message.text.strip()[7:].strip()
            clinic = self.get_clinic(message, rest)

            if not clinic:
                message.respond(HUB_DEMO_FAIL)
            else:
                # Fake like we need to prompt their clinic for results, as a means
                # to conduct user testing.  The mocker does not touch the database
                self.info("Initiating demo reports to clinic: %s" % clinic)
                self.fake_sending_dho_reports(clinic)
            return True
        elif message.text.strip().upper().startswith("PHODEMO"):
            rest = message.text.strip()[7:].strip()

            clinic = self.get_clinic(message, rest)
            if not clinic:
                message.respond(HUB_DEMO_FAIL)
            else:
                # Fake like we need to prompt their clinic for results, as a means
                # to conduct user testing.  The mocker does not touch the database
                self.info("Initiating demo reports to clinic: %s" % clinic)
                self.fake_sending_pho_reports(clinic)
            return True

    def get_clinic(self, message, code):
        clinic = None
        if code:
            # optionally allow the tester to pass in a clinic code
            try:
                clinic = Location.objects.get(slug__iexact=code)
            except Location.DoesNotExist:
                # maybe they just passed along some extra text
                pass
        if not clinic and message.connection.contact \
            and message.connection.contact.location:
                # They were already registered for a particular clinic
                # so assume they want to use that one.
                clinic = message.connection.contact.location
        return clinic

    def fake_send_dbs_recvd_at_lab_notification(self, clinic):
        hub_workers = Contact.active.filter(types=get_hub_worker_type(), location=clinic)
        for hub_woker in hub_workers:
            samples = random.randrange(4, 16, 1)
            my_lab = get_lab_name(hub_woker.location.parent)
            msg = ("Demo report:\n"+SAMPLES_RECEIVED_TODAY % {'name':hub_woker.name, 'lab_name':my_lab,
                   'count':samples, 'hub_name':hub_woker.location.name})
            OutgoingMessage(hub_woker.default_connection, msg).send()

    def fake_sending_hub_reports(self, clinic):
        hub_workers = Contact.active.filter(types=get_hub_worker_type(), location=clinic)
        today = date.today()
        month_ago = date(today.year, today.month, 1)-timedelta(days=1)        
        for hub_woker in hub_workers:
            name = hub_woker.name
            month = month_ago.strftime("%B")
            hub_name = hub_woker.location.name
            samples = random.randrange(16, 40, 1)
            results = random.randrange(16, 40, 1)
            district_name = clinic.parent.name

            msg = ("Demo report:\n"+DBS_SUMMARY % {'name':name, 'month':month,
                   'hub_name':hub_name, 'samples':samples,
                   'results':results, 'district_name':district_name})
            OutgoingMessage(hub_woker.default_connection, msg).send()

    def fake_sending_dho_reports(self, clinic):
        hub_workers = Contact.active.filter(types=get_district_worker_type(), location=clinic)
        today = date.today()
        month_ago = date(today.year, today.month, 1)-timedelta(days=1)
        for hub_woker in hub_workers:
            name = hub_woker.name
            month = month_ago.strftime("%B")
            samples = random.randrange(16, 40, 1)
            results = random.randrange(16, 40, 1)
            district_name = clinic.name
            msg = ("Demo report:\n%s, %s %s EID & Birth Totals\n DBS Totals sent: %s ***\nDBS "
                   "Results received; %s ***\nBirths registered; 34" % (name, month, district_name, samples, results))
            OutgoingMessage(hub_woker.default_connection, msg).send()

    def fake_sending_pho_reports(self, clinic):
        hub_workers = Contact.active.filter(types=get_province_worker_type(), location=clinic)
        today = date.today()
        month_ago = date(today.year, today.month, 1)-timedelta(days=1)
        for hub_woker in hub_workers:
            name = hub_woker.name
            month = month_ago.strftime("%B")
            samples = random.randrange(16,40,1)
            results = random.randrange(16,40,1)
            district_name = clinic.name
            msg = ("Demo report:\n%s, %s %s EID & Birth Totals\n DBS Totals sent: %s ***\nDBS "
            "Results received; %s ***\nBirths registered; 34" %(name,month,district_name,samples,results))
            OutgoingMessage(hub_woker.default_connection, msg).send()

