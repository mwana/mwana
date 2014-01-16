# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.translator.util import Translator
from datetime import date
from datetime import timedelta
from mwana.apps.labresults.messages import RIMINDMI_DEMO_FAIL
from mwana.apps.locations.models import Location
from mwana.const import get_cba_type
from rapidsms.log.mixin import LoggerMixin
from rapidsms.messages.outgoing import OutgoingMessage
from rapidsms.models import Contact
from mwana.apps.reminders.models import PatientEvent

_ = lambda x: x



class MockRemindMiUtility(LoggerMixin):
    """
    A mock reports utility.  This allows you to do some demo/training scripts
    while not writing any results data to the database.
    """

    def handle(self, message):
        if message.text.strip().upper().startswith("RMDEMO"):
            rest = message.text.strip()[6:].strip()
            clinic = self.get_clinic(message, rest)

            if not clinic:
                message.respond(RIMINDMI_DEMO_FAIL)
            else:
                self.info("Initiating demo remindmi to clinic: %s" % clinic)
                self.fake_sending_six_day_notification(clinic)
            return True

    def fake_sending_six_day_notification(self, clinic):
        translator = Translator()
        cbas = Contact.active.filter(types=get_cba_type(), location__parent=clinic)
        patients = PatientEvent.objects.filter(cba_conn__in=(cba.default_connection for cba in cbas)).distinct()
        
        if patients:
            patient_name = patients[0].patient.name
        else:
            patient_name = "Maria Malambo"
        
        appt_date = date.today() + timedelta(days=3)
        for cba in cbas:
            OutgoingMessage(cba.default_connection, _("Hi %(cba)s.%(patient)s is due for "
                                  "%(type)s clinic visit on %(date)s.Please "
                                  "remind them to visit %(clinic)s, then "
                                  "reply with TOLD %(patient)s"),
                                  cba=cba.name, patient=patient_name,
                                  date=appt_date.strftime('%d/%m/%Y'),
                                  clinic=clinic.name, type=translator.translate(cba.language, "6 day")).send()
                                  
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
