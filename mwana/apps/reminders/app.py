# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.translator.util import Translator
import re
import rapidsms
import datetime

from rapidsms.models import Contact
from rapidsms.contrib.scheduler.models import EventSchedule

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

    def start(self):
        self.schedule_notification_task()

    def schedule_notification_task(self):
        """
        Resets (removes and re-creates) the task in the scheduler app that is
        used to send notifications to CBAs.
        """
        callback = 'mwana.apps.reminders.tasks.send_notifications'

        #remove existing schedule tasks; reschedule based on the current setting from config
        EventSchedule.objects.filter(callback=callback).delete()
        EventSchedule.objects.create(callback=callback, hours=[12],
                                     minutes=[0])

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

    def _validate_cell(self, num):
        if len(num) == 10:
            if num[:2] == '08':
                backend_id = 3
            else:
                backend_id = 4
            valid_cell = True
        else:
            backend_id = None
            valid_cell = False
        return backend_id, valid_cell

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

        # handle mayi messages differently.
        if event_slug == "mayi":
            self.handle_mayi(msg, event)
            return True

        lang_code = None
        if msg.contact:
            cba_name = ' %s' % msg.contact.name
            lang_code = msg.contact.language
        else:
            cba_name = ''

        event_name = translator.translate(lang_code, event.name)

        date_str, patient_name, event_location_type = self._parse_message(msg)
        # if patient name is too long it's most likely the message sent was wrong
        if patient_name and len(patient_name) < 50:  # the date is optional
            if date_str:
                date = self._parse_date(date_str)
                if not date:
                    msg.respond(_("Sorry, I couldn't understand that date. "
                                "Please enter the date like so: "
                                "DDMMYY, for example: 271011"))
                    return True
            else:
                date = datetime.datetime.today()

            # make sure the birth date is not in the future
            if date > datetime.datetime.today():
                msg.respond(_("Sorry, you can not register a %s with a date "
                "after today's." % event.name.lower()))
                return True

            # fetch or create the patient
            if msg.contact and msg.contact.location:
                patient, created = Contact.objects.get_or_create(
                                            name=patient_name,
                                            location=msg.contact.location)
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
                    msg.respond(_("Thank you%(cba)s! You registered a %(descriptive_event)s for "
                        "%(name)s on %(date)s. You will be notified when "
                        "it is time for %(gender)s next clinic appointment."),
                        cba=cba_name, gender=gender,
                        date=date.strftime('%d/%m/%Y'), name=patient.name,
                        descriptive_event=descriptive_event.lower())
                else:
                    msg.respond(_("Thank you%(cba)s! You have successfully registered a %(event)s for "
                        "%(name)s on %(date)s. You will be notified when "
                        "it is time for %(gender)s next appointment at the "
                        "clinic."), cba=cba_name, gender=gender,
                        event=event_name.lower(),
                        date=date.strftime('%d/%m/%Y'), name=patient.name)
                return True

            patient.patient_events.create(event=event, date=date,
                                          cba_conn=msg.connection,
                                          notification_status="new",
                                          event_location_type=event_location_type)

            # TODO: This is temporal. In future responses will be same save for
            # the words facilty/home. Malawi/Zambia will have to agree on
            # the words to use
            if event_location_type:
                msg.respond(_("Thank you%(cba)s! You registered a %(descriptive_event)s for "
                    "%(name)s on %(date)s. You will be notified when "
                    "it is time for %(gender)s next clinic appointment."),
                    cba=cba_name, gender=gender,
                    date=date.strftime('%d/%m/%Y'), name=patient.name,
                    descriptive_event=descriptive_event.lower())
            else:
                msg.respond(_("Thank you%(cba)s! You have successfully registered a %(event)s for "
                    "%(name)s on %(date)s. You will be notified when "
                    "it is time for %(gender)s next appointment at the "
                        "clinic."), cba=cba_name, gender=gender,
                    event=event_name.lower(),
                    date=date.strftime('%d/%m/%Y'), name=patient.name)
        else:
            if event_slug == "mwana":
                self.HELP_TEXT = _("To register a birth, send %(event_upper)s <DATE> <MOTHERS NAME>.")
            msg.respond(_("Sorry, I didn't understand that. "
                "To add a %(event_lower)s, send %(event_upper)s <DATE> <NAME>."
                " The date is optional and is logged as TODAY if left out."),
                event_lower=event_name.lower(),
                event_upper=translator.translate(lang_code, event.name, 1).upper())
        return True

    def handle_mayi(self, msg, event):
        """Handles continuum of care submissions.
        """

        # Only allow registered HSA's to register mothers for care
        if not msg.contact:
            msg.respond(_("Please register as a Mobile agent to register mothers for care."
                          " send JOIN <HSA> <CLINIC CODE> <ZONE #> <YOUR NAME>"))
            return True

        if (len(msg.text.split()) > 4):
            part_msg, cell_number = msg.text.rsplit(" ", 1)
            msg.text = part_msg
            date_str, patient_name = self._parse_message(msg)
            msg.text = " ".join([part_msg, cell_number])
        else:
            date_str, patient_name = self._parse_message(msg)
            cell_number = "x"

        if patient_name:  # the date is not optional
            if date_str:
                date = self._parse_date(date_str)
                if not date:
                    msg.respond(_("Sorry, I couldn't understand that date. "
                                "Please enter the date like so: "
                                "DDMMYY, for example: 271011"))
                    return True
            else:
                msg.respond(_("Sorry, a date is required to register a mother."
                              "Please calculate the expected date of delivery "
                              "using the mothers LMP."))
                return True
            # fetch or create the patient
            if msg.contact and msg.contact.location:
                patient, created = Contact.objects.get_or_create(
                                            name=patient_name,
                                            location=msg.contact.location)

            # make sure the contact has the correct type (patient)
            patient_t = const.get_patient_type()
            if not patient.types.filter(pk=patient_t.pk).count():
                patient.types.add(patient_t)

            # validate mothers cell number
            backend_id, valid_cell = self._validate_cell(cell_number)
            # create patient_conn
            if valid_cell:
                cell_number = "+265" + cell_number[1:]
                patient_conn = Connection(backend_id=backend_id,
                                          identity=cell_number,
                                          contact_id=patient.id)
            else:
                patient_conn = None

            # make sure we don't create a duplicate patient event
            if msg.contact:
                cba_name = ' %s' % msg.contact.name
            else:
                cba_name = ''
            rsms_id = "Mi" + str(py_cupom.encode(patient.id, 5, True))
            if patient.patient_events.filter(event=event, date=date).count():
                #There's no need to tell the sender we already have them in the system.  Might as well just send a thank
                #you and get on with it.
                msg.respond(_("Thanks! You have registered "
                        "%(name)s's LMP as %(date)s. Her RemindMi_ID is %(remind_id)s, you will be notified for "
                              "%(gender)s next clinic appointment."), gender=event.possessive_pronoun,
                        date=date.strftime('%d/%m/%Y'), name=patient.name, remind_id=patient.remind_id)
                return True
            patient_event = patient.patient_events.create(event=event,
                                                  date=date,
                                                  cba_conn=msg.connection,
                                                  notification_status="cooc")
            if patient_conn is not None:
                patient_event.patient_conn=patient_conn
                patient_event.save()
            gender = event.possessive_pronoun
            msg.respond(_("Thanks! You have registered "
                        "%(name)s's LMP as %(date)s. Her RemindMi_ID is %(rsms_id)s, you will be notified for "
                        "%(gender)s next clinic appointment."), gender=gender,
                        rsms_id=rsms_id,
                        date=date.strftime('%d/%m/%Y'), name=patient.name)
            patient.remind_id = rsms_id
            patient.save()
        else:
            msg.respond(_("Sorry, I didn't understand that. To register a mother for care, send "
                      "MAYI <DELIVERY_DATE> <MOTHERS_NAME> <OPTIONAL_MOTHERS_CELL_NUMBER>"))

        return True
