# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.birthcertification.models import CertificateNotification
from mwana.apps.birthcertification.models import RegistrationReminder
from datetime import date
from datetime import datetime
from datetime import timedelta
import logging

from mwana.apps.birthcertification.models import Agent
from mwana.apps.birthcertification.models import Certification
from mwana.apps.reminders.models import PatientEvent
from mwana.util import get_clinic_or_default
from rapidsms.messages.outgoing import OutgoingMessage



logger = logging.getLogger(__name__)

_ = lambda s:s

REG_MESSAGE = _(("Hello %(agent)s, please remind %(patient)s to register"
                " birth of the child at %(location)s"))


CERT_MESSAGE = _(("Hello %(agent)s, please tell %(patient)s to collect"
                " the birth certicate for the child at %(location)s"))

def send_birth_registration_reminder(router):
    """
    Sends reminder to Agents to tell parents to register a birth at facility
    """
    logger.debug("In send_birth_registration_reminder")

    window_period = 16 # days. we don't wan't to include very old births
    
    date_back = date.today() - timedelta(days=window_period)

    # create certifications for new births, later may apply other filters such us
    # location.
    for pe in PatientEvent.objects.filter(certification=None, date__gt=date_back):
        Certification(birth=pe).save() # not so worried about records being commited immediately


    for certification in Certification.objects.filter(status='nb'): # new birth
        recipients = Agent.active.filter(
                                         contact__location=\
                                         certification.birth.patient.location)\
                                         .distinct()
        patient = certification.birth.patient

        
        if not recipients:
            logger.debug('No Agents to get reminders to register birth for %s at %s'
                         % (certification.birth.patient.name,
                         certification.birth.patient.location))
            return

        for agent in recipients:
            msg = REG_MESSAGE % {'agent':agent.contact.name, 'patient':patient.name,
            'location':get_clinic_or_default(patient)}
            OutgoingMessage(agent.contact.default_connection, msg).send()

            RegistrationReminder.objects.create(certification=certification, agent=agent)

        certification.reg_notification_date = datetime.now()
        certification.save()

def send_certicate_ready_notification(router):
    """
    Sends notification to collect certificate at facility once ready
    """
    logger.debug("In send_certicate_ready_notification")



    for certification in Certification.objects.filter(status='ready'):
        recipients = Agent.active.filter(
                                         contact__location=\
                                         certification.birth.patient.location)\
                                         .distinct()
        patient = certification.birth.patient


        if not recipients:
            logger.debug('No Agents to get notications to collect certicate for %s at %s'
                         % (certification.birth.patient.name,
                         certification.birth.patient.location))
            return

        for agent in recipients:
            msg = CERT_MESSAGE % {'agent':agent.contact.name, 'patient':patient.name,
            'location':get_clinic_or_default(patient)}
            OutgoingMessage(agent.contact.default_connection, msg).send()

            CertificateNotification.objects.create(certification=certification, agent=agent)

        certification.certificate_notification_date = datetime.now()
        certification.save()
