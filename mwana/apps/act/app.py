# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.act.messages import CLIENT_MESSAGE_CHOICES
from mwana.apps.act.models import Appointment
from mwana.apps.act.models import PHARMACY_TYPE
from mwana.apps.act.models import LAB_TYPE
from mwana.apps.act.models import FlowAppointment
from datetime import date, timedelta
from datetime import datetime
from django.conf import settings
from mwana.apps.act.models import CHW
from mwana.apps.act.models import Client
from mwana.apps.act.models import FlowCHWRegistration
from mwana.apps.act.models import FlowClientRegistration
from mwana.apps.act.models import ReminderMessagePreference
from mwana.apps.locations.models import Location
from mwana.util import LocationCode
import rapidsms
from rapidsms.contrib.scheduler.models import EventSchedule
from rapidsms.contrib.messagelog.models import Message
import uuid


SUPPORTED_PHONE_LINES = ['97', '96']
INVALID_PHONE_NUMBER_RESPONSE = "Sorry %(number)s is not a valid Airtel or MTN number. Reply with correct number"
INVALID_NRC_RESPONSE = "Sorry %(number)s is not a valid NRC number. Reply with correct NRC number"


class App(rapidsms.apps.base.AppBase):
    def start(self):
        self.schedule_notification_task()

    def schedule_notification_task(self):
        """
        Resets (removes and re-creates) the task in the scheduler app that is
        used to send notifications to CBAs.
        """
        callback = 'mwana.apps.act.tasks.send_notifications'

        #remove existing schedule tasks; reschedule based on the current setting from config
        EventSchedule.objects.filter(callback=callback).delete()
        EventSchedule.objects.create(callback=callback, hours=range(24),
                                     minutes=range(60))

    def valid_phone(self, text):
        try:
            int(text)
        except ValueError:
            return None
        if len(text) not in (len('+260979123456'), len('260979123456'), len('0979123456'),
                             len('979123456')):
            return None
        if text[-9:-7] not in SUPPORTED_PHONE_LINES:
            return None
        return '+260' + text[-9:]

    def valid_national_id(self, text):
        id = text.replace('\\', '/').replace(' ', '/').strip()
        tokens = id.split('/')
        if len(tokens) != 3:
            return None
        serial, district, country = tokens
        if country != '1':
            return None

        if 6 != len(serial):
            return None
        try:
            int(serial)
            int(district)
            int(country)
        except ValueError:
            return None

        return id

    def handle(self, msg):
        if not msg.text:
            return False

        cleaned_text = msg.text.strip().lower()[:30]
        #-------------------------#
        # Handle CHW Registration #
        #-------------------------#
        open_flows = FlowCHWRegistration.objects.filter(connection=msg.connection, open=True,
                                                        start_time__lte=datetime.now()). \
            filter(valid_until__gte=datetime.now())

        if open_flows:
            flow = FlowCHWRegistration.objects.filter(connection=msg.connection, open=True,
                                                      start_time__lte=datetime.now()). \
                get(valid_until__gte=datetime.now())
            if not flow.name:
                flow.name = cleaned_text.title()
                flow.save()
                msg.respond("Thank you %s. Now reply with your NRC" % flow.name)
                return True
            elif not flow.national_id:
                national_id = self.valid_national_id(cleaned_text)
                if not national_id:
                    msg.respond(INVALID_NRC_RESPONSE, number=cleaned_text.replace(' ', '/'))
                    return True

                flow.national_id = national_id
                flow.save()
                msg.respond("Thank you %s. Now reply with your clinic code" % flow.name)
                return True
            elif not flow.location:
                clinic_code = LocationCode(cleaned_text)
                location_type = clinic_code.get_location_type()
                locations = Location.objects.filter(slug__iexact=cleaned_text[:6],
                                                    type__slug__in=location_type)
                if not locations:
                    msg.respond(
                        ("Sorry, I don't know about a clinic with code %(code)s. "
                         "Please check your code and try again."),
                        code=cleaned_text)
                    return True
                flow.location = locations[0]

                flow.save()
                chw = CHW()
                chw.connection = flow.connection
                chw.name = flow.name
                chw.location = flow.location
                chw.national_id = flow.national_id
                chw.phone = flow.connection.identity
                chw.phone_verified = True
                chw.uuid = str(uuid.uuid1())

                chw.save()
                flow.delete()
                msg.respond("%(name)s you have successfully joined as CHW for the ACT Program "
                            "from %(clinic)s clinic and your NRC is %(nrc)s. If this is NOT correct send 4444 and register again",
                            name=chw.name, clinic=chw.location.name, nrc=chw.national_id)
                return True

        #--------------------------------#
        # Handle ACT Client Registration #
        #--------------------------------#
        open_flows = FlowClientRegistration.objects.filter(community_worker__connection=msg.connection, open=True,
                                                           start_time__lte=datetime.now()). \
            filter(valid_until__gte=datetime.now())

        if open_flows:
            flow = FlowClientRegistration.objects.filter(community_worker__connection=msg.connection, open=True,
                                                         start_time__lte=datetime.now()). \
                get(valid_until__gte=datetime.now())
            if not flow.national_id:
                if len(cleaned_text) < 8 or not (cleaned_text[:6].isdigit()):
                    reply = "Sorry %s is not a valid unique ID. Reply with correct unique ID." % cleaned_text
                    last = ''
                    if settings.NATIONAL_CLIENT_IDS:
                        last = " Valid unique ID's are %s" % ', '.join(settings.NATIONAL_CLIENT_IDS)

                    msg.respond(reply + last)
                    return True
                elif Client.objects.filter(national_id=cleaned_text):
                    client = Client.objects.filter(national_id=cleaned_text)[0]
                    msg.respond(
                        "A client, %(client)s, with ID %(id)s already exists. Reply with correct ID or send HELP CLIENT if you need to be assisted",
                        client=settings.GET_ORIGINAL_TEXT(client.name), id=cleaned_text)
                    return True
                flow.national_id = cleaned_text
                flow.save()
                msg.respond(
                    "You have submitted client's ID %s. Now reply with the client's name" % flow.national_id)
                return True
            elif not flow.name:
                name = cleaned_text.title()
                if len(name) < 4:
                    msg.respond("%s does not look like a valid name. Reply with a valid name" % name)
                    return True
                flow.name = name
                flow.save()
                msg.respond(
                    "You have submitted client's name as %s. Now reply with client's date of birth like <DAY> <MONTH> <YEAR> e.g. 12 04 2006 for 12 April 2006" % flow.name)
                return True
            elif not flow.dob:
                tokens = cleaned_text.split()
                if len(tokens) != 3:
                    msg.respond(
                        "%s does not look like a valid date. Reply with client's correct date of birth like <DAY> <MONTH> <YEAR> e.g. 12 04 1997 for 12 April 1997." % cleaned_text)
                    return True
                try:
                    day, month, year = [int(i) for i in tokens]
                except ValueError:
                    msg.respond(
                        "%s does not look like a valid date. Reply with client's correct date of birth like <DAY> <MONTH> <YEAR> e.g. 12 04 1997 for 12 April 1997." % cleaned_text)
                    return True
                if year < 1900:
                    msg.respond(
                        "Date %s has an invalid year. Reply with client's correct date of birth like <DAY> <MONTH> <YEAR> e.g. 12 04 1997 for 12 April 1997." % cleaned_text)
                    return True
                elif month < 1 or month > 12:
                    msg.respond(
                        "Date %s has an invalid month. Reply with client's correct date of birth like <DAY> <MONTH> <YEAR> e.g. 12 04 1997 for 12 April 1997." % cleaned_text)
                    return True
                try:
                    dob = date(year, month, day)
                except ValueError:
                    msg.respond(
                        "%s does not look like a valid date. Reply with client's correct date of birth like <DAY> <MONTH> <YEAR> e.g. 12 04 1997 for 12 April 1997." % cleaned_text)
                    return True
                if dob > date.today():
                    msg.respond(
                        "Sorry, client's date of birth %s is after today's. Reply with client's correct date of birth like <DAY> <MONTH> <YEAR> e.g. 12 04 1997 for 12 April 1997." % cleaned_text)
                    return True
                if dob == date.today():
                    msg.respond(
                        "Sorry, client's date of birth %s cannot be equal to today's. Reply with client's correct date of birth like <DAY> <MONTH> <YEAR> e.g. 12 04 1997 for 12 April 1997." % cleaned_text)
                    return True
                flow.dob = dob
                flow.save()
                msg.respond(
                    "You have submitted client's date of birth as %s. Now reply with the client's gender, F for Female or M if Male" % dob.strftime(
                        '%d %b %Y'))
                return True
            elif not flow.sex:
                response = cleaned_text.lower()
                if response not in ('m', 'f', 'male', 'female'):
                    msg.respond(
                        "Sorry, client's gender must be F or M. Reply with the client's gender, F for Female or M if Male")
                    return True
                if response in ('f', 'female'):
                    flow.sex = 'f'
                elif response in ('m', 'male'):
                    flow.sex = 'm'
                flow.save()
                msg.respond(
                    "You have submitted client's gender as %s. Will client be receiving SMS messages, Reply with Y for Yes or N for No?" % flow.get_sex_display())
                return True
            elif flow.can_receive_messages == None:
                response = cleaned_text.lower()
                if response not in ('y', 'n', 'yes', 'no'):
                    msg.respond(
                        "Sorry, I din't understand that. Reply with Y if client will be receiving SMS messages or N if not")
                    return True
                if response in ('n', 'No'):
                    flow.can_receive_messages = False
                elif response in ('y', 'yes'):
                    flow.can_receive_messages = True
                flow.save()
                msg.respond(
                    "Thank you %s. Now reply with the client's phone number or N/A if client or caregiver does not have a phone" % flow.community_worker.name)
                return True
            elif not flow.phone:
                phone = self.valid_phone(cleaned_text)
                if not phone and cleaned_text.lower() not in ('none', 'na', 'n/a', 'n\a', 'n a'):
                    msg.respond(INVALID_PHONE_NUMBER_RESPONSE, number=cleaned_text)
                    return True
                if not phone:
                    flow.phone = 'None' # Don't leave field blank
                else:
                    flow.phone = phone
                flow.save()
                if flow.phone and flow.phone != 'None':
                    msg.respond(
                        "Client's name is %(name)s, ID is %(id)s, DOB is %(dob)s, gender is %(sex)s, phone # is %(phone)s, will receive SMS: %(can_receive_sms)s. Reply with Yes if "
                        "this is correct or No if not", phone=flow.phone, name=flow.name,
                        id=flow.national_id, dob=flow.dob.strftime('%d %B %Y'),
                        sex='Female' if flow.sex == 'f' else 'Male',
                        can_receive_sms='Yes' if flow.can_receive_messages else 'No')
                else:
                    msg.respond(
                        "Client's name is %(name)s, ID is %(id)s, DOB is %(dob)s, gender is %(sex)s. Reply with Yes if "
                        "this is correct or No if not", name=flow.name,
                        id=flow.national_id, dob=flow.dob.strftime('%d %B %Y'),
                        sex='Female' if flow.sex == 'f' else 'Male')
                return True
            elif cleaned_text in ('yes', 'y'):
                client_uuid = str(uuid.uuid1())
                today = datetime.today()
                yesterday = today - timedelta(days=1)

                client = Client.objects.create(national_id=flow.national_id,
                                               name=settings.GET_CLEANED_TEXT(flow.name),
                                               uuid=client_uuid,
                                               alias=(''.join([item[0] for item in
                                                               flow.name.split()]) + '-' + flow.national_id).upper(),
                                               dob=flow.dob,
                                               location=flow.community_worker.location,
                                               community_worker=flow.community_worker,
                                               phone=flow.phone if flow.phone != 'None' else None,
                                               sex=flow.sex,
                                               can_receive_messages=flow.can_receive_messages
                )

                msg.respond("Thank you %(chw)s. You have successfully registered the client %(client)s"
                    , chw=flow.community_worker.name, client=flow.name)

                if flow.phone:
                    # TODO: Test this
                    phone_verified = Message.objects.filter(direction='I', date__lte=yesterday,
                                                            connection__identity__endswith=flow.phone,
                                                            text__istartswith='ACT YES').exists()
                    if phone_verified:
                        client.phone_verified = True
                        client.can_receive_messages = True
                        client.save()

                flow.delete()
                return True
            elif cleaned_text in ('no', 'n'):
                msg.respond("You can start a new submission by sending ACT CLIENT or ACT CHILD")
                flow.delete()
                return True
            else:
                if flow.phone and flow.phone != 'None':
                    msg.respond(
                        "Client's name is %(name)s, ID is %(id)s, DOB is %(dob)s, gender is %(sex)s, phone # is %(phone)s, will receive SMS: %(can_receive_sms)s. Reply with Yes if "
                        "this is correct or No if not", phone=flow.phone, name=flow.name,
                        id=flow.national_id, dob=flow.dob.strftime('%d %B %Y'),
                        sex='Female' if flow.sex == 'f' else 'Male',
                        can_receive_sms='Yes' if flow.can_receive_messages else 'No')
                else:
                    msg.respond(
                        "Client's name is %(name)s, ID is %(id)s, DOB is %(dob)s, gender is %(sex)s. Reply with Yes if "
                        "this is correct or No if not", name=flow.name,
                        id=flow.national_id, dob=flow.dob.strftime('%d %B %Y'),
                        sex='Female' if flow.sex == 'f' else 'Male')
                return True
            #--------------------------------#
        # Handle Appointment Registration #
        #--------------------------------#
        open_flows = FlowAppointment.objects.filter(community_worker__connection=msg.connection, open=True,
                                                    start_time__lte=datetime.now()). \
            filter(valid_until__gte=datetime.now())

        if open_flows:
            flow = FlowAppointment.objects.filter(community_worker__connection=msg.connection, open=True,
                                                  start_time__lte=datetime.now()). \
                get(valid_until__gte=datetime.now())
            if not flow.client:
                clients = Client.objects.filter(national_id=cleaned_text)
                if not clients:
                    msg.respond(
                        "Client with ID %(id)s does not exist. Please verify the ID or to regsiter a new client send ACT CHILD",
                        id=cleaned_text)
                    return True

                client = Client.objects.filter(national_id=cleaned_text)[0]

                flow.client = client
                flow.save()
                msg.respond(
                    "ID %(id)s is for %(client)s. Now reply with the appointment date "
                    "like <DAY> <MONTH> <YEAR> e.g. 12 04 2018 for 12 April 2018.", id=client.national_id,
                    client=settings.GET_ORIGINAL_TEXT(client.name))
                return True

            elif not flow.date:
                tokens = cleaned_text.split()
                if len(tokens) != 3:
                    msg.respond(
                        "%s does not look like a valid date. Reply with correct date like <DAY> <MONTH> <YEAR> e.g. 12 04 2008 for 12 April 2018." % cleaned_text)
                    return True
                try:
                    day, month, year = [int(i) for i in tokens]
                except ValueError:
                    msg.respond(
                        "%s does not look like a valid date. Reply with client's correct date of birth like <DAY> <MONTH> <YEAR> e.g. 12 04 2008 for 12 April 2018." % cleaned_text)
                    return True
                if year < 1900:
                    msg.respond(
                        "Date %s has an invalid year. Reply with correct date like <DAY> <MONTH> <YEAR> e.g. 12 04 2008 for 12 April 2018." % cleaned_text)
                    return True
                elif month < 1 or month > 12:
                    msg.respond(
                        "Date %s has an invalid month. Reply with correct date like <DAY> <MONTH> <YEAR> e.g. 12 04 2008 for 12 April 2018." % cleaned_text)
                    return True
                try:
                    appointment_date = date(year, month, day)
                except ValueError:
                    msg.respond(
                        "%s does not look like a valid date. Reply with correct date like <DAY> <MONTH> <YEAR> e.g. 12 04 2008 for 12 April 2018." % cleaned_text)
                    return True
                if appointment_date < date.today():
                    msg.respond(
                        "Sorry, you cannot register an oppointment with date before today's. %s is in the past" % cleaned_text)
                    return True

                flow.date = appointment_date
                flow.save()
                msg.respond(
                    "You have submitted appointment date as %s. Now reply with the type of appointment, L for Lab visit or P if Pharmacy visit" % appointment_date.strftime(
                        '%d %b %Y'))
                return True
            elif not flow.type:
                response = cleaned_text.lower()
                if response not in ('l', 'p', 'lab', 'pharmacy'):
                    msg.respond(
                        "Sorry, appointment type must be L or P. Reply with the correct appointment type, L for Lab visit or P if Pharmacy visit")
                    return True
                if response in ('l', 'lab'):
                    flow.type = LAB_TYPE
                elif response in ('p', 'pharmacy'):
                    flow.type = PHARMACY_TYPE

                prefs = ReminderMessagePreference.objects.filter(client=flow.client, visit_type=flow.type)
                if prefs:
                    flow.message_id = prefs[0].message_id
                flow.save()
                if flow.message_id:
                    msg.respond(
                        "You have submitted %(type)s appointment for "
                        "%(client)s for %(date)s. Reply with Yes if this is"
                        " correct or No if not", type=flow.get_type_display(),
                        client=settings.GET_ORIGINAL_TEXT(flow.client.name), date=flow.date.strftime('%d %B %Y'))
                else:
                    msg.respond(
                        "Now submit the client's preferred message type for %(type)s. Refer to Job Aid on Message Preferences, e.g. m1 or m2 or m3 etc",
                        type=flow.get_type_display(),
                        client=settings.GET_ORIGINAL_TEXT(flow.client.name), date=flow.date)
                return True
            elif flow.message_id == None:
                response = cleaned_text.lower()
                if response not in CLIENT_MESSAGE_CHOICES.keys():
                    msg.respond("Sorry, %(id)s is not a valid preferred message type. Valid types are %(valid)s",
                                id=response, valid=', '.join(CLIENT_MESSAGE_CHOICES.keys()))
                    return True
                pref, created = ReminderMessagePreference.objects.get_or_create(client=flow.client,
                                                                                visit_type=flow.type,
                                                                                message_id=response)
                flow.message_id = response
                flow.save()
                msg.respond(
                    "You have submitted %(type)s appointment for "
                    "%(client)s for %(date)s. Reply with Yes if this is"
                    " correct or No if not", type=flow.get_type_display(),
                    client=settings.GET_ORIGINAL_TEXT(flow.client.name), date=flow.date.strftime('%d %B %Y'))
                return True
            elif cleaned_text in ('yes', 'y'):
                _uuid = str(uuid.uuid1())

                record, _ = Appointment.objects.get_or_create(client=flow.client,
                                                              cha_responsible=flow.community_worker, type=flow.type,
                                                              date=flow.date, uuid=_uuid)

                msg.respond("Thank you %(chw)s. You have successfully registered a "
                            "%(type)s appointment for %(client)s on %(date)s"
                        , chw=record.cha_responsible.name, client=settings.GET_ORIGINAL_TEXT(record.client.name),
                            type=record.get_type_display(), date=record.date.strftime('%d %B %Y'))

                flow.delete()
                return True
            elif cleaned_text in ('no', 'n'):
                msg.respond("You can start a new submission by sending ACT VISIT")
                flow.delete()
                return True
            else:
                msg.respond(
                    "You have submitted %(type)s appointment for "
                    "%(client)s for %(date)s. Reply with Yes if this is"
                    " correct or No if not", type=flow.get_type_display(),
                    client=settings.GET_ORIGINAL_TEXT(flow.client.name), date=flow.date.strftime('%d %B %Y'))
                return True

        return False
