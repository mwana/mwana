# vim: ai ts=4 sts=4 et sw=4

from mwana.apps.reminders.models import PatientEvent
from mwana.apps.reminders.models import Event
import logging

from mwana import const
from mwana.apps.labresults.util import is_eligible_for_results
from mwana.apps.stringcleaning.inputcleaner import InputCleaner
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.models import Contact

logger = logging.getLogger(__name__)
from datetime import date
from datetime import timedelta

_ = lambda x: x


class MwanaForHandler(KeywordHandler):
    """
    Register a birth on behalf of someone
    """

    keyword = "mwanafor|birthfo|mwanafo|birthfo"

    HELP_TEXT = "To register a birth on behalf of a CBA, send MWANAFOR <CBA-PHONE-#> <LOCATION-TYPE> <DAY> <MONTH> <YEAR> <NAME>"
    INELIGIBLE = "Sorry, you are NOT allowed to register a birth on behalf of anyone. If you think this message is a mistake reply with keyword HELP"


    def help(self):
        self.respond(self.HELP_TEXT)

    def handle(self, text):
        if not (self.msg.contact and self.msg.contact.is_active and self.msg.contact.is_help_admin):
            # essentially checking for an active clinic_worker
            self.respond(self.INELIGIBLE)
            return

        alternative_date_separators = ('/', '.', '-')
        my_text = text.strip()
        for separator in alternative_date_separators:
            my_text = my_text.replace(separator, ' ')

        tokens = my_text.split()

        if len(tokens) < 5:
            self.help()
            return

        # verify phone number length
        if len(tokens[0]) < 9:
            self.help()
            return

        # phone number must have format [+]\d{9, 12}
        if not tokens[0][1:].isdigit:
            self.help()
            return

        location_type = None
        if tokens[1].lower() in ['f', 'h']:
            cba_phone = tokens[0]
            location_type = {'f': 'cl', 'h': 'hm'}[tokens[1].lower()]
            day = tokens[2]
            month = tokens[3]
            year = tokens[4]
            if not all(it.isdigit() for it in [day, month, year]):
                self.help()
                return
            name = " ".join(tokens[5:])
        elif tokens[1].isdigit():
            cba_phone = tokens[0]
            day = tokens[1]
            month = tokens[2]
            year = tokens[3]
            if not all(it.isdigit() for it in [day, month, year]):
                self.help()
                return
            name = " ".join(tokens[4:])

        name = name.title()
        day = int(day)
        if day not in range(32):
            self.respond("Sorry, make sure you type the day correctly.")
            return

        month = int(month)
        if month not in range(13):
            self.respond("Sorry, make sure you type the month correctly.")
            return

        year = int(year)

        today = date.today()

        # make sure the birth date is not in the future
        if year > today.year:
            self.respond("Sorry, you cannot register a birth with a date "
                         "after today's.")
            return True

        dob = date(year, month, day)
        # make sure the date is not unreasonably too old
        if dob < today - timedelta(days=1000):
            self.respond(_("Sorry, make sure you enter the year correctly."
                           " %(date_entered)s is too old. We are in %(current_date)s."),
                         date_entered=date.year, current_date=today.year)
            return True

        try:
            cba = \
                Contact.active.get(connection__identity__contains=cba_phone,
                                   types=const.get_cba_type())
        except Contact.DoesNotExist:
            self.respond('The phone number %(phone)s does not belong to any'
                         ' CBA. Make sure you typed it '
                         'correctly', phone=cba_phone)
            return True
        except Contact.MultipleObjectsReturned:
            self.respond("Sorry, there are multiple connections with phone number %(phone)s"
                , phone=cba_phone)
            return True

        pe = PatientEvent.objects.filter(cba_conn=cba.default_connection, patient__name__iexact=name, date=dob)

        if pe:
            self.respond("%(patient)s with DOB %(dob)s is already for/by %(cba)s (%(cba_phone)s).",
                         patient=name, dob=dob.strftime('%d/%m/%Y'),
                         cba=cba.name,
                         cba_phone=cba.default_connection.identity)
            return

        patient = Contact.objects.create(name=name, location=cba.location)
        patient.types.add(const.get_patient_type())
        #patient.save()
        event = Event.objects.get(slug__icontains='birth')
        PatientEvent.objects.create(cba_conn=cba.default_connection, patient=patient,
                                    date=dob, event_location_type=location_type,
                                    event=event)

        descriptive_event = ("%(type)s %(event)s" % {'event': event.name.lower(), 'type':
                                                                  {'cl': 'facility', 'hm': 'home'}
                                                                     .get(location_type, '')}).strip()
        self.respond('Thank you %(sender)s! You have registered a %(descriptive_event)s for %(patient)s on %(dob)s'
                     ' on behalf of %(cba)s.',
                     dob=dob.strftime('%d/%m/%Y'), sender=self.msg.contact.name,
                     descriptive_event=descriptive_event, cba=cba.name, patient=patient.name)

