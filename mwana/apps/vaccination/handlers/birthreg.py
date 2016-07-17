# vim: ai ts=4 sts=4 et sw=4

from mwana.apps.vaccination.commons import Parser
from mwana.util import get_clinic_or_default
from datetime import timedelta
from datetime import date
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from mwana.apps.vaccination.models import VaccinationSession
from mwana.apps.vaccination.models import Client
from mwana.apps.vaccination.models import Appointment


_ = lambda s: s

UNREGISTERED = _("Sorry, you must be registered before you can register a child. If you think this message is a mistake, respond with keyword 'HELP'")

SORRY = _("Sorry, we didn't understand that message.")
HELP_TEXT = _("To register a birth for immunization tracking send BIRTHREG <BABY_ID> <GENDER> <DOB> <MOTHER_NAME> <MOTHER_AGE> E.g. BIRTHREG 21314/16 F 2/8/2016 Jane Moonga 25")


class BirthRegHandler(KeywordHandler, Parser):

    keyword = "BIRTHREG|BITHREG|BETHREG|BABY"

    def help(self):
        self.respond(HELP_TEXT)

    def handle(self, text):
        if not self.msg.contact:
            self.respond(UNREGISTERED)
            return True

        tokens = text.strip().split()

        if len(tokens) < 5 or len(tokens) > 8:
            self.help()
            return True

        client_number = tokens[0]
        gender_str = tokens[1]
        birth_date_str = tokens[2]
        mother_name = " ".join(tokens[3:-1]).title()
        mother_age_str = tokens[-1]

        gender_map = {'f': 'f', 'female': 'f', 'm': 'm', 'male':'m'}

        if (not self.PATIENT_ID_RE.match(client_number)) or len(client_number) < 4 or len(client_number) > 20:
            self.respond(_("Sorry, '%s', is not a valid Child's ID. If you think this message is a mistake reply with keyword HELP." % client_number))
            return True

        if not gender_str.lower() in gender_map:
            self.respond(_("%s is not a correct value for gender. Enter gender as F or M" % gender_str))
            return True
        else:
            gender = gender_map[gender_str.lower()]

        if not self.DATE_RE.match(birth_date_str):
            self.respond(_("Sorry, I couldn't understand the date '%s'. Enter date like DAY/MONTH/YEAR, e.g. %s" % (birth_date_str, date.today().strftime('%d/%m/%Y'))))
            return True
        else:
            dob = self._parse_date(birth_date_str)
            if not dob:
                self.respond(_("Sorry, I couldn't understand the date '%s'. Enter date like DAY/MONTH/YEAR, e.g. %s" % (birth_date_str, date.today().strftime('%d/%m/%Y'))))
                return True
            elif dob > date.today():
                self.respond(_("Sorry, you cannot register a birth with a date "
                             "after today's."))
                return True

        if len(mother_name) < 3 or len(mother_name) > 50:
            self.respond(_("Sorry, '%s', is not a valid name" % mother_name))
            return True

        if (not mother_age_str.isdigit()) or int(mother_age_str) < 13 or int(mother_age_str) >= 50:
            self.respond(_("Sorry, '%s', is not a valid number for mother's age" % mother_age_str))
            return True
        else:
            mother_age = int(mother_age_str)

        client = Client()
        client.client_number = client_number
        client.gender = gender
        client.birth_date = dob
        client.mother_name = mother_name
        client.mother_age = mother_age
        client.location = self.msg.contact.location

        exact_duplicate = False

        if Client.objects.filter(client_number=client.client_number, location=client.location):
            existing_client = Client.objects.get(client_number=client.client_number, location=client.location)
            if existing_client.birth_date != client.birth_date or existing_client.gender != client.gender\
                or existing_client.mother_name != client.mother_name or existing_client.mother_age != client.mother_age:
                self.respond(_("There is already a baby registered with BabyID: %(id)s, Gender: %(sex)s, DOB: %(dob)s, "
                               "Mother's Name: %(name)s, Mother's Age: %(age)s, Clinic: %(loc)s"), id=existing_client.client_number,
                             sex=existing_client.get_gender_display(), dob=existing_client.birth_date.strftime('%d/%m/%Y'), name=existing_client.mother_name,
                             age=existing_client.mother_age, loc=get_clinic_or_default(existing_client))
                return True
            else:
                exact_duplicate = True

        if not exact_duplicate:
            client.save()
            for session in VaccinationSession.objects.filter(predecessor=None):
                appointment = Appointment()
                appointment.client = client
                appointment.vaccination_session = session
                appointment.cba_responsible = self.msg.contact
                appointment.scheduled_date = client.birth_date + timedelta(days=session.min_child_age)
                appointment.save()

        self.respond(_("Thank you %(cba)s! You have successfully registered a baby with "
                       "ID %(id)s, Gender %(gender)s, DOB %(dob)s for %(name)s aged %(age)s."),
                     cba=self.msg.contact.name,
                     id = client.client_number,
                     gender=client.get_gender_display(),
                     dob = client.birth_date.strftime('%d/%m/%Y'),
                     name = client.mother_name,
                     age=mother_age)
        