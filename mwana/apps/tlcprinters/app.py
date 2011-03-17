import logging
import rapidsms
import re
from django.conf import settings
from mwana.apps.tlcprinters.models import MessageConfirmation
from rapidsms.contrib.scheduler.models import EventSchedule

logger = logging.getLogger(__name__)

class App (rapidsms.apps.base.AppBase):
    confirm_regex = r'Confirm SMS:(.+)'

    def start (self):
        self.schedule_send_results_to_printer_task()

    def schedule_send_results_to_printer_task(self):
        callback = 'mwana.apps.tlcprinters.tasks.send_results_to_printer'
        # remove existing schedule tasks; reschedule based on the current setting
        EventSchedule.objects.filter(callback=callback).delete()
        EventSchedule.objects.create(callback=callback, hours=[7, 8, 9, 10, 13, 14, 16], minutes=[50],
                                     days_of_week=[0, 1, 2, 3, 4])
        

    
    def handle(self, message):
        """
        Handle the Confirm SMS messages sent by TLC printers.
        """
        match = re.match(self.confirm_regex, message.text, re.IGNORECASE)
        if not match:
            return False
        try:
            seq_num = int(match.group(1).strip(), 16)
        except ValueError:
            logger.warning('Received Confirm SMS message, but message ID %s'
                           'did not parse as hexadecimal.' % match.group(1))
            seq_num = None
        if seq_num:
            try:
                msg_conf = MessageConfirmation.objects.filter(
                                                              seq_num=seq_num,
                                                              connection=message.connection,
                                                              confirmed=False,
                                                              ).order_by('-sent_at')[0]
            except IndexError: #DoesNotExist never happens with filter()
                msg_conf = None
                logger.warning('No message confirmation found for '
                               'connection=%s and seq_num=%s' %
                               (message.connection, seq_num))
            if msg_conf:
                logger.debug('Marking message confirmation %s as confirmed' %
                             msg_conf)
                msg_conf.confirmed = True
                msg_conf.save()
        return True
