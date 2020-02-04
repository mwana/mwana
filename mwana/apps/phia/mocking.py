# vim: ai ts=4 sts=4 et sw=4
import datetime
import mwana.const as const
import random
from django.conf import settings
from mwana.apps.labresults.messages import ALREADY_COLLECTED
from mwana.apps.labresults.messages import BAD_PIN
from mwana.apps.labresults.messages import DEMO_FAIL
from mwana.apps.labresults.messages import INSTRUCTIONS
from mwana.apps.labresults.messages import RESULTS_PROCESSED
from mwana.apps.labresults.messages import RESULTS_READY
from mwana.apps.labresults.messages import SELF_COLLECTED
from mwana.apps.labresults.models import Result
from mwana.apps.locations.models import Location
from rapidsms.log.mixin import LoggerMixin
from rapidsms.messages.outgoing import OutgoingMessage
from rapidsms.models import Contact


RESULTS = "Here are your results: "


def build_results_messages(results):
    """
    From a list of lab results, build a list of messages reporting
    their status
    """
    result_strings = []
    max_len = settings.MAX_SMS_LENGTH
    # if messages are updates to requisition ids
    for res in results:
        result_strings.append("**** %s;%s" % (res.requisition_id,
                                  res.result))

    result_text, remainder = combine_to_length(result_strings,
                                               length=max_len-len(RESULTS))
    first_msg = RESULTS + result_text
    responses = [first_msg]
    while remainder:
        next_msg, remainder = combine_to_length(remainder)
        responses.append(next_msg)
    return responses

def build_tlc_messages(results):
    """
    
    """
    result_strings = []
    max_len = settings.MAX_SMS_LENGTH
    # if messages are updates to requisition ids
    for res in results:
        result_strings.append("%s%s ****" % (res.result, res.requisition_id))

    result_text, remainder = combine_to_length(result_strings,
                                               length=max_len-len(RESULTS))
    first_msg = "LTC: " + result_text
    responses = [first_msg]
    while remainder:
        next_msg, remainder = combine_to_length(remainder)
        responses.append(next_msg)
    return responses


def combine_to_length(list, delimiter=". ", length=None):
    """
    Combine a list of strings to a maximum of a specified length, using the
    delimiter to separate them.  Returns the combined strings and the
    remainder as a tuple.
    """
    if length is None:
        length = settings.MAX_SMS_LENGTH
    if not list:  return ("", [])
    if len(list[0]) > length:
        raise Exception("None of the messages will fit in the specified length of %s" % length)

    msg = ""
    for i in range(len(list)):
        item = list[i]
        new_msg = item if not msg else msg + delimiter + item
        if len(new_msg) <= length:
            msg = new_msg
        else:
            return (msg, list[i:])
    return (msg, [])


class MockResultUtility(LoggerMixin):
    """
    A mock data utility.  This allows you to script some demo/testing scripts
    while not reading or writing any results data to the database.
    """

    waiting_for_pin = {}
    last_collectors = {}

  

    def handle(self, message):
        if message.text.strip().upper().startswith("ROR DEMO"):
            rest = message.text.strip()[8:].strip()
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
        elif message.connection.contact and const.get_phia_worker_type() in message.connection.contact.types.all() \
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
        contacts = Contact.active.filter(types=const.get_phia_worker_type(), location=clinic)
        results = get_fake_results(3, clinic)
        for contact in contacts:
            
            msg = OutgoingMessage(connection=contact.default_connection,
                                  template="%(clinic)s has %(count)s results ready. Please reply to this SMS with your pin code to retrieve them.",
                                  clinic=contact.location.name, count=len(results))
            msg.send()
            self._mark_results_pending(results, msg.connection)


    def _mark_results_pending(self, results, connection):
        self.waiting_for_pin[connection] = results

class MockLtcUtility(LoggerMixin):
    """
    A mock data utility.  This allows you to script some demo/testing scripts
    while not reading or writing any results data to the database.
    """

    waiting_for_pin = {}
    last_collectors = {}



    def handle(self, message):
        if message.text.strip().upper().startswith("LTC DEMO"):
            rest = message.text.strip()[8:].strip()
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
                    responses = build_tlc_messages(results)

                    for resp in responses:
                        message.respond(resp)

                    message.respond("Please record these details in your LTC Register immediately and promptly delete them from your phone. Thank you again!")

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
        elif message.connection.contact and const.get_phia_worker_type() in message.connection.contact.types.all() \
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
        contacts = Contact.active.filter(types=const.get_phia_worker_type(), location=clinic)
        results = get_fake_tlc_details(2, clinic)
        for contact in contacts:

            msg = OutgoingMessage(connection=contact.default_connection,
                                  template="%(clinic)s has %(count)s ALTC & 1 passive participant to link to care. Please reply with your PIN code to get details of ALTC participants.",
                                  clinic=contact.location.name, count=len(results) )
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
    result_choices = ["CD200;VL500", "CD250;VL300", "CD650;VL100",  "CD750;VL56"]
    if clinic.type.slug in const.ZONE_SLUGS:
        clinic = clinic.parent
    for i in range(count):
        requisition_id = requisition_id_format.format(id=(current_requisition_id + i),
                                                      clinic=clinic.slug)
        status = random.choice(notification_status_choices)
        result = Result(requisition_id=requisition_id, clinic=clinic,
                        # make sure we get at least one of each possible result
#                        result=result_choices[i % len(result_choices)],
                        result=result_choices[i % len(result_choices)],
                        collected_on=datetime.datetime.today(),
                        entered_on=datetime.datetime.today(),
                        notification_status=status)
        results.append(result)
    return results


def get_fake_tlc_details(count, clinic, starting_requisition_id=9990,
                     requisition_id_format=None,
                     notification_status_choices=("new", )):

    results = []
    if requisition_id_format is None:
        requisition_id_format = getattr(settings, "RESULTS160_FAKE_ID_FORMAT",
                                        "{id:04d}")
    current_requisition_id = starting_requisition_id
    # strip off indeterminate/inconsistent, as those results won't be sent
    result_choices = ["Banana Nkonde;14 Munali, Lusaka;", "Sante Banda;12 Minestone, Lusaka;"]
    if clinic.type.slug in const.ZONE_SLUGS:
        clinic = clinic.parent
    for i in range(count):
        requisition_id = requisition_id_format.format(id=(current_requisition_id + i),
                                                      clinic=clinic.slug)
        status = random.choice(notification_status_choices)
        result = Result(requisition_id=requisition_id, clinic=clinic,
                        # make sure we get at least one of each possible result
#                        result=result_choices[i % len(result_choices)],
                        result=result_choices[i % len(result_choices)],
                        collected_on=datetime.datetime.today(),
                        entered_on=datetime.datetime.today(),
                        notification_status=status)
        results.append(result)
    return results

