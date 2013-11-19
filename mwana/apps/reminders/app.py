# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.translator.util import Translator
import re
import rapidsms
import datetime

from rapidsms.models import Contact

from mwana.apps.reminders import models as reminders
from mwana.apps.reminders.mocking import MockRemindMiUtility
from mwana.malawi.lib import py_cupom
from mwana import const

# In RapidSMS, message translation is done in OutgoingMessage, so no need
# to attempt the real translation here.  Use _ so that ./manage.py makemessages
# finds our text.
_ = lambda s: s

translator = Translator()


class App(rapidsms.apps.base.AppBase):
    queryset = reminders.Event.objects.values_list('slug', flat=True)

    #TODO move this to database
    LOCATION_TYPES = {'f': 'cl', 'h': 'hm', 'clinic': 'cl', 'cl': 'cl',
                        'hm': 'hm', 'fa': 'cl', 'home': 'hm', 'facility': 'cl'}

    DATE_RE = re.compile(r"[\d/.-]+")
    HELP_TEXT = _("To add a %(event_lower)s, send %(event_upper)s <DATE> <NAME>."\
                " The date is optional and is logged as TODAY if left out.")
    DATE_FORMATS = (
        '%d/%m/%y',
        '%d/%m/%Y',
        '%d/%m',
        '%d%m%y',
        '%d%m%Y',
        '%d%m',
    )

    UNREGISTERED = "Please register before reporting births or mothers. Send JOIN for more help."

    def _parse_date(self, date_str):
        """
        Tries each of the supported date formats in turn.  If the year was not
        specified, it defaults to the current year.
        """
        date = None
        date_str = re.sub('[. -]', '/', date_str)
        while '//' in date_str:
            date_str = date_str.replace('//', '/')
        for format in self.DATE_FORMATS:
            try:
                date = datetime.datetime.strptime(date_str, format)
            except ValueError:
                pass
            if date:
                break
        if date:
            # is there a better way to do this? if no year was specified in
            # the string, it defaults to 1900
            if date.year == 1900:
                date = date.replace(year=datetime.datetime.now().year)
        return date

    def _parse_message(self, msg):
        """
        Attempts to parse the message iteratively; regular expressions are not
        greedy enough and will, if the date doesn't match for some reason, end
        up generating messages like "You have successfully registered a birth
        for 24. 06. 2010" (since the date is optional).
        """

        keyword = msg.text.strip().split()[0].lower()
        rest = msg.text.strip().split()[1:]

        #TODO This is a quick way of implementing registration of
        #facility and/or home births. Use a longer term solution later
        if 'mwana' in keyword and len('mwana') < len(keyword):
            keyword = keyword.replace("mwana", "mwana ", True)

        to_parse = keyword.split() + rest
        parts = to_parse[1:]  # exclude the keyword (e.g., "birth")
        date_str = ''
        name = ''
        location_type = None

        if parts and parts[0].lower() in self.LOCATION_TYPES:
            location_type = self.LOCATION_TYPES[parts[0].lower()]
            parts = parts[1:]

        for part in parts:
            if self.DATE_RE.match(part):
                if date_str: date_str += ' '
                date_str += part
            else:
                if name: name += ' '
                name += part
        return date_str, name, location_type

    def _get_event(self, slug):
        """
        Returns a single matching event based on the slug, allowing for
        multiple |-separated slugs in the "slug" field in the database.
        """
        for event in reminders.Event.objects.filter(slug__icontains=slug):
            keywords = [k.strip().lower() for k in event.slug.split('|')]
            if slug in keywords:
                return event

    def handle(self, msg):
        """
        Handles the actual adding of events.  Other simpler commands are done
        through handlers.

        This needs to be an app because the "keywords" for this command are
        dynamic (i.e., in the database) and, while it's possible to make a
        handler with dynamic keywords, the API doesn't give you a way to see
        what keyword was actually typed by the user.
        """

        mocker = MockRemindMiUtility()

        if mocker.handle(msg):
            return True

        if not msg.text:
            return False
        event_slug = msg.text.split()[0].lower()
        event = self._get_event(event_slug)
        if not event:
            return False

        lang_code = None
        if msg.connections[0].contact:
            cba_name = ' %s' % msg.connections[0].contact.name
            lang_code = msg.connections[0].contact.language
        else:
            cba_name = ''

        event_name = translator.translate(lang_code, event.name)

        date_str, patient_name, event_location_type = self._parse_message(msg)
        # if patient name is too long it's most likely the message sent was wrong
        if patient_name and len(patient_name) < 50:  # the date is optional
            if date_str:
                date = self._parse_date(date_str)
                if not date:
                    msg_no_date = "Sorry, I couldn't understand that date. "\
                                  "Please enter the date like so: "\
                                  "DDMMYY, for example: 271011"
                    msg.respond(msg_no_date)
                    return True
            else:
                date = datetime.datetime.today()

            # make sure the birth date is not in the future
            if date > datetime.datetime.today():
                msg_future = "Sorry, you can not register a %s with a date "\
                             "after today's." % event.name.lower()
                msg.respond(msg_future)
                return True

            # fetch or create the patient
            if msg.connections[0].contact and msg.connections[0].contact.location:
                patient, created = Contact.objects.get_or_create(
                                            name=patient_name,
                                            location=msg.connections[0].contact.location)
            else:
                patient = Contact.objects.create(name=patient_name)

            # make sure the contact has the correct type (patient)
            patient_t = const.get_patient_type()
            if not patient.types.filter(pk=patient_t.pk).count():
                patient.types.add(patient_t)

            location_type = {"cl": "facility", "hm": "home"}\
                        [event_location_type] if event_location_type else ""

            descriptive_event = "%(location_type)s %(event)s" % {'event': event,
            'location_type': location_type}

            descriptive_event = translator.translate(lang_code, descriptive_event)
            gender = translator.translate(lang_code, event.possessive_pronoun)

            if patient.patient_events.filter(event=event, date=date).count():
                #There's no need to tell the sender we already have them in the system.  Might as well just send a thank
                #you and get on with it.

                # TODO: This is temporal. In future responses will be same save for
                # the words facilty/home. Malawi/Zambia will have to agree on
                # the words to use
                if event_location_type:
                    msg_registered = """Thank you%(cba)s! You registered a %(descriptive_event)s for %(name)s on %(date)s. You will be notified when it is time for %(gender)s next clinic appointment.""" % dict(
                        cba=cba_name, gender=gender,
                        date=date.strftime('%d/%m/%Y'), name=patient.name,
                        descriptive_event=descriptive_event.lower())
                    msg.respond(msg_registered)
                else:
                    msg_success = """Thank you%(cba)s! You have successfully registered a %(event)s for %(name)s on %(date)s. You will be notified when it is time for %(gender)s next appointment at the clinic.""" % dict(cba=cba_name, gender=gender,
                        event=event_name.lower(),
                        date=date.strftime('%d/%m/%Y'), name=patient.name)
                    msg.respond(msg_success)
                return True

            patient.patient_events.create(event=event, date=date,
                                          cba_conn=msg.connection,
                                          notification_status="new",
                                          event_location_type=event_location_type)

            # TODO: This is temporal. In future responses will be same save for
            # the words facilty/home. Malawi/Zambia will have to agree on
            # the words to use
            if event_location_type:
                r_msg = "Thank you%(cba)s! You registered a %(descriptive_event)s for %(name)s on %(date)s. You will be notified when it is time for %(gender)s next clinic appointment." % dict(
                    cba=cba_name, gender=gender,
                    date=date.strftime('%d/%m/%Y'), name=patient.name,
                    descriptive_event=descriptive_event.lower())
                msg.respond(r_msg)
            else:
                r_msg = "Thank you%(cba)s! You have successfully registered a %(event)s for %(name)s on %(date)s. You will be notified when it is time for %(gender)s next appointment at the clinic." % dict(cba=cba_name, gender=gender,
                    event=event_name.lower(),
                    date=date.strftime('%d/%m/%Y'), name=patient.name)
                msg.respond(r_msg)
        else:
            if event_slug == "mwana":
                self.HELP_TEXT = "To register a birth, send %(event_upper)s <DATE> <MOTHERS NAME>." % dict(event_upper = event_slug.upper())
                msg.respond(self.HELP_TEXT)
                return True
            msg_error = "Sorry, I didn't understand that. To add a %(event_lower)s, send %(event_upper)s <DATE> <NAME>. The date is optional and is logged as TODAY if left out." % dict(
                event_lower=event_name.lower(),
                event_upper=translator.translate(lang_code, event.name, 1).upper())
            msg.respond(msg_error)
        return True
