# vim: ai ts=4 sts=4 et sw=4
import smtplib
from email.mime.text import MIMEText
from django.conf import settings
import logging

class EmailSender:
    def connect(self):
        host = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        user = settings.EMAIL_HOST_USER
        password = settings.EMAIL_PASSWORD
        host.ehlo()
        host.starttls()
        host.login(user, password)
        return host, user

    def close(self, host):
        host.quit()

    def m_send(self, to_list, subject, message_text):
        logger = logging.getLogger(__name__)
        logger.info('Attempting to send email %s\n\nto %s' %(message_text[:100], to_list))

        msg = MIMEText(message_text)
        msg['Subject'] = subject

        host, user = self.connect()
        host.sendmail(user, to_list, msg.as_string())
        self.close(host)

    def send(self, to_list, subject, message_text, host=None, user=None):
        if (not host) or (not user):
            self.m_send(to_list, subject, message_text)
            return

        logger = logging.getLogger(__name__)
        logger.info('Attempting to send email %s\n\nto %s' %(message_text[:100], to_list))
        msg = MIMEText(message_text)
        msg['Subject'] = subject
        host.sendmail(user, to_list, msg.as_string())

        