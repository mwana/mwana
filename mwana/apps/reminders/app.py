# vim: ai ts=4 sts=4 et sw=4
import re
import rapidsms
import datetime

from rapidsms.models import Contact
from rapidsms.contrib.scheduler.models import EventSchedule, ALL

from mwana.apps.contactsplus.models import ContactType
from mwana.apps.reminders import models as reminders
from mwana.apps.labresults.mocking import MockRemindMiUtility
from mwana import const

# In RapidSMS, message translation is done in OutgoingMessage, so no need
# to attempt the real translation here.  Use _ so that ./manage.py makemessages
# finds our text.
_ = lambda s: s

class App(rapidsms.apps.base.AppBase):
    queryset = reminders.Event.objects.values_list('slug', flat=True)
    
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
    
    def schedule_notification_task (self):
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
        parts = msg.text.split()[1:] # exclude the keyword (e.g., "birth")
        date_str = ''
        name = ''
        for part in parts:
            if self.DATE_RE.match(part):
                if date_str: date_str += ' '
                date_str += part
            else:
                if name: name += ' '
                name += part
        return date_str, name

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
        date_str, patient_name = self._parse_message(msg)
        if patient_name: # the date is optional
            if date_str:
                date = self._parse_date(date_str)
                if not date:
                    msg.respond(_("Sorry, I couldn't understand that date. "
                                "Please enter the date like so: "
                                "DAY MONTH YEAR, for example: 23 04 2010"))
                    return
            else:
                date = datetime.datetime.today()

            # make sure the birth date is not in the future
            if date > datetime.datetime.today():
                msg.respond(_("Sorry, you can not register a %s with a date "
                "after today's." % event.name.lower()))
                return

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

            # make sure we don't create a duplicate patient event
            if msg.contact:
                cba_name = ' %s' % msg.contact.name
            else:
                cba_name = ''
            if patient.patient_events.filter(event=event, date=date).count():
                #There's no need to tell the sender we already have them in the system.  Might as well just send a thank
                #you and get on with it.
                msg.respond(_("Thank you%(cba)s! You have successfully registered a %(event)s for "
                        "%(name)s on %(date)s. You will be notified when "
                        "it is time for %(gender)s next appointment at the "
                        "clinic."), cba=cba_name, gender=event.possessive_pronoun,
                        event=event.name.lower(),
                        date=date.strftime('%d/%m/%Y'), name=patient.name)
                return
            patient.patient_events.create(event=event, date=date,
                                          cba_conn=msg.connection, notification_status="new")
            gender = event.possessive_pronoun
            msg.respond(_("Thank you%(cba)s! You have successfully registered a %(event)s for "
                        "%(name)s on %(date)s. You will be notified when "
                        "it is time for %(gender)s next appointment at the "
                        "clinic."), cba=cba_name, gender=gender,
                        event=event.name.lower(),
                        date=date.strftime('%d/%m/%Y'), name=patient.name)
        else:
            msg.respond(_("Sorry, I didn't understand that.") + " " +
                        self.HELP_TEXT % {'event_lower': event.name.lower(),
                                          'event_upper': event.name.upper()})
        return True
