# vim: ai ts=4 sts=4 et sw=4
from datetime import date, timedelta
import logging

from django.core.exceptions import ObjectDoesNotExist
from django import forms

from rapidsms.models import Contact, Connection, Backend
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler

from mwana.apps.reminders import models as reminders
# from mwana.malawi.lib import py_cupom
from mwana import const


logger = logging.getLogger(__name__)

MAYI_HELP = """To report an expectant mother send:
MAYI <EDD:DDMMYY> <MOTHERS_NAME> <MOTHERS_PHONE|X> <HIV_STATUS:P|N|U>"""
UNREGISTERED = "Please register as an HSA before submitting MAYI reports."\
               " Send JOIN for help on how to join."
TOO_FEW_TOKENS = "It seems you have not sent enough data. Please put an X"\
                 " where there is no data or send MAYI to"\
                 "check the format you need to send."
GARBLED_MSG = "Sorry, I don't understand: %s. Please send MAYI"\
              "to check the format."


class MayiHandler(KeywordHandler):

    keyword = 'mayi'

    def help(self):
        """Respond with the MAYI help message."""
        self.respond(MAYI_HELP)

    def _get_tokens(self, text):
        """Splits the text into the expected parts."""
        text = text.strip()
        tokens = {'edd': '', 'name': '', 'first_name': '', 'last_name': '',
                  'phone': '', 'dob': '', 'hiv_status': ''}
        validate_tokens = True
        try:
            token_list = text.split()
            if len(token_list) < 5:
                logger.debug("missing data")
                self.respond(TOO_FEW_TOKENS)
                validate_tokens = False
            if len(token_list) == 5:
                tokens['edd'] = token_list[0]
                tokens['first_name'] = token_list[1]
                tokens['last_name'] = token_list[2]
                tokens['phone'] = token_list[3]
                tokens['hiv_status'] = token_list[4]
                tokens['name'] = ' '.join(
                    [tokens['first_name'], tokens['last_name']])
            if len(token_list) == 6:
                tokens['edd'] = token_list[0]
                tokens['first_name'] = token_list[1]
                tokens['last_name'] = token_list[2]
                tokens['dob'] = token_list[3]
                tokens['phone'] = token_list[4]
                tokens['hiv_status'] = token_list[5]
                tokens['name'] = ' '.join(list(tokens['first_name'],
                                               tokens['last_name']))
            return tokens, validate_tokens
        except:
            reformat_msg = GARBLED_MSG % text
            self.respond(reformat_msg)
            return None, False

    def _validate_cell(self, num):
        if num.strip().upper() in ['X', 'XX']:
            return None, False
        try:
            num = int(num)
        except ValueError:
            # register no number if not valid number
            return None, False
        # only accept 10 digit numbers for now
        if len(str(num)) == 9:
            if str(num)[:1] == '8':
                backend_name = 'tnm'
            elif str(num)[:1] == '9':
                backend_name = 'zain'
            valid_cell = True
        else:
            backend_name = None
            valid_cell = False
        return backend_name, valid_cell

    def _validate_tokens(self, tokens):
        """ Check that tokens sent are valid"""

        errors = []
        # check that date is not too early or too late or not valid
        date_error = "Sorry, I don't understand %s. Please"\
                     " try a format like 311213" % tokens['edd']
        try:
            date_field = forms.DateField(
                input_formats=('%d%m%y', '%d/%m/%y', '%d-%m-%y',
                               '%d%m%Y', '%d/%m/%Y', '%d-%m-%Y'),
                error_messages={'invalid': date_error}
                # TODO: add validators for min max date
            )
            tokens['edd'] = date_field.clean(tokens['edd'])
            if tokens['edd'] < date.today():
                early_date_msg = "Sorry, it seems that date has already"\
                                 "passed. Plese enter a date in the next"\
                                 "9 months."
                errors.append(early_date_msg)
            elif tokens['edd'] > (date.today() + timedelta(270)):
                late_date_msg = "Sorry, the mother needs to be already"\
                                "expectant before registering for reminders."
                errors.append(late_date_msg)
        except forms.ValidationError:
            errors.append(date_error)
            self.respond(date_error)

        # pass on name checking
        # check phone number
        try:
            backend_name, valid_cell = self._validate_cell(tokens['phone'])
            if valid_cell:
                tokens['phone'] = "+265" + tokens['phone'][1:]
                tokens['backend_name'] = backend_name
            else:
                tokens['phone'] = None
        except:
            pass
        # check hiv status
        status_error_msg = "Sorry, I don't understand %s as a status."\
                           "Status will be set to U = Unknown."
        if tokens['hiv_status'].strip().upper() in ['P', 'N', 'U']:
            tokens['hiv_status'] = tokens['hiv_status'].upper()
        else:
            tokens['hiv_status'] = None
            errors.append(status_error_msg)
        return tokens, errors

    def _get_event(self, slug):
        """
        Returns a single matching event based on the slug, allowing for
        multiple |-separated slugs in the "slug" field in the database.
        """
        for event in reminders.Event.objects.filter(slug__icontains=slug):
            keywords = [k.strip().lower() for k in event.slug.split('|')]
            if slug in keywords:
                return event

    def _get_backend(self, backend_name):
        """Returns a matching backend based on the name."""
        return Backend.objects.filter(name__iexact=backend_name)[0]

    def handle(self, text):
        """Handle the mayi submission."""
        # only allow registered users to submit

        if self.msg.connections[0].contact is not None:
            healthworker = self.msg.connections[0].contact
        else:
            self.respond(UNREGISTERED)
            return True

        # get the event
        event = self._get_event('cooc')
       # get the message parts
        tokens, validate_tokens = self._get_tokens(text)

        # only proceed if all is ok
        if not validate_tokens:
            return

        # validate the tokens
        data, errors = self._validate_tokens(tokens)
        if len(errors) > 0:
            error_msgs = ' '.join(errors)
            return self.respond(error_msgs)

        # create the patient
        if healthworker and healthworker.location:
            patient, created = Contact.objects.get_or_create(
                name=data['name'], location=healthworker.location,
                first_name=data['first_name'],
                last_name=data['last_name']
            )

        patient_t = const.get_patient_type()
        if not patient.types.filter(pk=patient_t.pk).count():
            patient.types.add(patient_t)

        if data['phone'] is not None:
            backend = self._get_backend(data['backend_name'])
            patient_conn = Connection(backend=backend,
                                      identity=data['phone'],
                                      contact_id=patient.id)
        else:
            patient_conn = None

        if healthworker:
            hsa_name = ' %s' % healthworker.name
        if patient.patient_events.filter(event=event,
                                         date=data['edd']).count():
            # send thank you message although patient
            # already has event registered
            thanks_msg = "Thanks%(hsa_name)s! You have registered %(name)s's"\
                         " expected delivery date as %(date)s. You will be "\
                         "notified for her next clinic appointment."\
                         % dict(name=patient.name,
                                date=data['edd'].strftime('%d/%m/%Y'),
                                hsa_name=hsa_name)
            self.msg.respond(thanks_msg)
            if patient_conn is not None:
                mayi_msg = "Dear %(name)s, you have been registered to"\
                           " receive reminders for care by %(hsa_name)s. You "\
                           "will be notified of your next clinic appointments."\
                           % dict(name=patient.name, hsa_name=hsa_name)
                self.msg.respond(mayi_msg)
            return True

        patient_event = patient.patient_events.create(
            event=event,
            date=data['edd'],
            cba_conn=self.msg.connections[0],
            notification_status="cooc")
        if patient_conn is not None:
            patient_event.patient_conn = patient_conn
            patient_event.save()
            mayi_msg = "Dear %(name)s, you have been registered to"\
                       " receive reminders for care by %(hsa_name)s. You "\
                       "will be notified of your next clinic appointments."\
                       % dict(name=patient.name, hsa_name=hsa_name)
            self.msg.respond(mayi_msg)

        new_mayi = "Thanks%(hsa_name)s! You have registered %(name)s's "\
                   "expected delivery date as %(date)s. You will be notified"\
                   " for her next clinic appointment." % dict(
                       name=data['name'],
                       date=data['edd'].strftime('%d/%m/%Y'),
                       hsa_name=hsa_name)
        return self.msg.respond(new_mayi)
