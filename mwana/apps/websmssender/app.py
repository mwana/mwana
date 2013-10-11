# vim: ai ts=4 sts=4 et sw=4
import logging
import rapidsms
# from rapidsms.contrib.scheduler.models import EventSchedule


logger = logging.getLogger(__name__)

# class App (rapidsms.apps.base.AppBase):


    # def start (self):
        # self.schedule_webblaster_report_task()

    # def schedule_webblaster_report_task(self):
        # callback = 'mwana.apps.websmssender.tasks.send_webblaster_report'
        # EventSchedule.objects.filter(callback=callback).delete()
        # EventSchedule.objects.create(callback=callback, hours=[8, 13, 16], minutes=[25],
                                     # days_of_week=[0, 1, 2, 3, 4, 5, 6])
