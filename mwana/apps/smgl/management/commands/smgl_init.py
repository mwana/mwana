from django.core.management.base import BaseCommand
from scheduler.models import EventSchedule

class Command(BaseCommand):
    help = "Initialize static data for SMGL"

    def handle(self, *args, **options):
        # currently just the schedules
        _update_schedules(log_to_console=True)
        

def _update_schedules():
    
    reminders = ["mwana.apps.smgl.reminders.send_followup_reminders",
                 "mwana.apps.smgl.reminders.send_non_emergency_referral_reminders",
                 "mwana.apps.smgl.reminders.send_emergency_referral_reminders",
                 "mwana.apps.smgl.reminders.send_upcoming_delivery_reminders"]
    for func_abspath in reminders:
        try:
            schedule = EventSchedule.objects.get(callback=func_abspath)
            schedule.hours = [8] # 8 in GMT is 10 in zambia
            schedule.minutes = [0]
        except EventSchedule.DoesNotExist:
            schedule = EventSchedule(callback=func_abspath,
                                     hours=[8],
                                     minutes=[0])
            schedule.save()
