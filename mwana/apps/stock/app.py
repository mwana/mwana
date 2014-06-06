# vim: ai ts=4 sts=4 et sw=4
import logging
import rapidsms
from rapidsms.contrib.scheduler.models import EventSchedule

logger = logging.getLogger(__name__)

class App (rapidsms.apps.base.AppBase):

    def start (self):
        self.schedule_low_stock_notification_task()

    def schedule_low_stock_notification_task(self):
        callback = 'mwana.apps.stock.tasks.send_stock_below_threshold_notification'
        EventSchedule.objects.filter(callback=callback).delete()
        EventSchedule.objects.create(callback=callback, hours=[10, 15], minutes=[15],
                                     days_of_week=[0, 1, 2, 3, 4])
    