# vim: ai ts=4 sts=4 et sw=4
import smtplib
from email.mime.text import MIMEText
from django.conf import settings
import logging

class EmailSender:
    def send(self, recipient, subject, message_text):
        logger = logging.getLogger(__name__)
        logger.info('Attempting to send email %s\n\nto %s' %(message_text[:100], recipient))
        host = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        user = settings.EMAIL_HOST_USER
        password = settings.EMAIL_PASSWORD

        msg = MIMEText(message_text)
        msg['Subject'] = subject



        host.ehlo()
        host.starttls()
        host.login(user, password)
        host.sendmail(user, recipient, msg.as_string())
        host.quit()