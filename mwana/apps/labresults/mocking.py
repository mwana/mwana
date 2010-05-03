from mwana.apps.labresults.messages import build_results_messages, INSTRUCTIONS, \
    RESULTS_READY, BAD_PIN, RESULTS_PROCESSED, DEMO_FAIL, ALREADY_COLLECTED, \
    SELF_COLLECTED
from mwana.apps.labresults.models import Result
from mwana.apps.labresults.util import is_eligible_for_results
from rapidsms.contrib.locations.models import Location
from rapidsms.log.mixin import LoggerMixin
from rapidsms.messages.outgoing import OutgoingMessage
from rapidsms.models import Contact
import datetime
import mwana.const as const
import random


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
        
    
def get_fake_results(count, clinic, starting_requisition_id=25, requisition_id_format="%04d",
                     notification_status_choices=("new",)):
    """Fake results for demos and trainings"""
    results = []
    current_requisition_id = starting_requisition_id
    for i in range(count-1):
        results.append(
            Result(requisition_id=requisition_id_format % (current_requisition_id + i), 
                   clinic=clinic, 
                   result=random.choice(Result.RESULT_CHOICES)[0],
                   collected_on=datetime.datetime.today(),
                   entered_on=datetime.datetime.today(), 
                   notification_status=random.choice(notification_status_choices),
                   sample_id = "lb0" + str(i+1),
                   result_detail = random.choice(("equipment is down", "still processing","best known to us"))))
    blankres=Result(requisition_id='030',
                   clinic = clinic,
                   collected_on=datetime.datetime.today(),
                   entered_on=datetime.datetime.today(),
                   notification_status=random.choice(notification_status_choices),
                   sample_id = "lb04")
    results.append(blankres)
    return results
