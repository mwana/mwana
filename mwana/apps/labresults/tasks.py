from mwana import const
from mwana.apps.labresults.models import Result
from rapidsms import router

def send_results_notification (self):
    clinics_with_results =\
      Result.objects.filter(notification_status__in=['new', 'notified'])\
                            .values_list("clinic", flat=True).distinct()
    labresults_app = router.router.get_app(const.LAB_RESULTS_APP)        
    for clinic in clinics_with_results:
        labresults_app.notify_clinic_pending_results(clinic)
        
