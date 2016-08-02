# vim: ai ts=4 sts=4 et sw=4

from mwana.apps.vaccination.models import ReportingTable
from datetime import date
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from mwana.apps.vaccination.models import VaccinationSession
from mwana.apps.vaccination.models import Client
from mwana.apps.vaccination.models import Appointment
from mwana.util import get_clinic_or_default
from mwana.apps.vaccination.commons import Parser

_ = lambda s: s

UNREGISTERED = _("Sorry, you must be registered before you can report a vaccination session'")
SORRY = _("Sorry, we didn't understand that message.")
HELP_TEXT = _("To report first vaccination for a child send <SESSION6> <Baby ID> <DATE OF VACCINATION> e.g SESSION6  123/16 23/8/2016")


class DangerSignHandler(KeywordHandler, Parser):

    keyword = "Danger Sign|DangerSign|Dager Sign|DagerSign|Danger"
    
    def help(self):
        self.respond(HELP_TEXT)

    def handle(self, text):
        if not self.msg.contact:
            self.respond(UNREGISTERED)
            return True

        tokens = text.strip().split()

        if len(tokens) != 2:
            self.help()
            return True

        client_number = tokens[0]        
        event_date_str = tokens[1]

        if not self.DATE_RE.match(event_date_str):
            self.respond(_("Sorry, I couldn't understand the date '%s'. Enter date like DAY/MONTH/YEAR, e.g. 17/07/2016" % event_date_str))
            return True
        else:
            vac_date = self._parse_date(event_date_str)
            if not vac_date:
                self.respond(_("Sorry, I couldn't understand the date '%s'. Enter date like DAY/MONTH/YEAR, e.g. 17/07/2016" % event_date_str))
                return True
            elif vac_date > date.today():
                self.respond(_("Sorry, you cannot report a danger sign with a date "
                             "after today's."))
                return True


        if not Client.objects.filter(client_number=client_number, location=self.msg.contact.location).exists():
            if not Client.objects.filter(client_number=client_number, location=get_clinic_or_default(self.msg.contact)).exists():
                self.respond(_("Sorry, I don't know a child with ID %(id)s at %(loc)s. If you think this message is a mistake reply with keyword HELP"), id=client_number, loc=get_clinic_or_default(self.msg.contact))
                return True
            else:
                client = Client.objects.get(client_number=client_number, location=get_clinic_or_default(self.msg.contact))
        else:
            client = Client.objects.get(client_number=client_number, location=self.msg.contact.location)

        session6 = VaccinationSession.objects.get(session_id='s6')

        appointment = Appointment.objects.get(client=client, vaccination_session=session6)
        if appointment.actual_date == None:
            appointment.actual_date = vac_date
            appointment.save()

        ReportingTable.objects.get_or_create(appointment=appointment, reported_visit_date=vac_date)
        self.respond(_("Thank you %(cba)s! You have reported '%(s6)s' for baby with "
                       "ID %(id)s and vaccination date %(vac_date)s."),
                     cba=self.msg.contact.name,
                     id = client.client_number,
                     s6=session6.__unicode__(),
                     vac_date = vac_date.strftime('%d/%m/%Y')
                     )


    