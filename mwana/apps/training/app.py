import logging
import mwana.const as const
import rapidsms
from django.conf import settings
from mwana.apps.labresults.messages import *
from mwana.apps.labresults.models import Result
from rapidsms.contrib.scheduler.models import EventSchedule
from rapidsms.messages import OutgoingMessage
from rapidsms.models import Contact

logger = logging.getLogger(__name__)

class App (rapidsms.App):


    def start (self):
        self.schedule_endof_training_notification_task()


    def schedule_endof_training_notification_task(self):
        callback = 'mwana.apps.training.tasks.send_endof_training_notification'
        # remove existing schedule tasks; reschedule based on the current setting
        EventSchedule.objects.filter(callback=callback).delete()
        EventSchedule.objects.create(callback=callback, hours=[16], minutes=[35],
                                     days_of_week=[0, 1, 2, 3, 4])




    def _updated_results(self, clinic):
        if settings.SEND_LIVE_LABRESULTS:
            return Result.objects.filter(clinic=clinic,
                                   notification_status='updated')
        else:
            return Result.objects.none()

    def notify_clinic_of_changed_records(self, clinic):
        """Notifies clinic of the new status for changed results."""
        changed_results = []
        updated_results = self._updated_results(clinic)
        if not updated_results:
            return
        for updated_result in updated_results:
            if updated_result.record_change:
                changed_results.append(updated_result)

        if not changed_results:
            return
        contacts = Contact.active.filter(location=clinic,
                                         types=const.get_clinic_worker_type())
        if not contacts:
            self.warning("No contacts registered to receive results at %s! "
                         "These will go unreported until clinic staff "
                         "register at this clinic." % clinic)
            return

        RESULTS_CHANGED     = "URGENT: A result sent to your clinic has changed. Please send your pin, get the new result and update your logbooks."
        if len(changed_results) > 1:
            RESULTS_CHANGED     = "URGENT: Some results sent to your clinic have changed. Please send your pin, get the new results and update your logbooks."

        all_msgs = []
        help_msgs = []

        for contact in contacts:
            msg = OutgoingMessage(connection=contact.default_connection,
                                  template=RESULTS_CHANGED)
            all_msgs.append(msg)

        contact_details = []
        for contact in contacts:
            contact_details.append("%s:%s" % (contact.name, contact.default_connection.identity))

        if all_msgs:
            self.send_messages(all_msgs)
            self._mark_results_pending(changed_results,
                                       (msg.connection for msg in all_msgs))

            for help_admin in Contact.active.filter(is_help_admin=True):
                h_msg = OutgoingMessage(
                            help_admin.default_connection,
                            "Make a followup for changed results %s: %s. Contacts = %s" %
                            (clinic.name, ";****".join("ID=" + res.requisition_id + ", Result="
                            + res.result + ", old value=" + res.old_value for res in changed_results),
                            ", ".join(contact_detail for contact_detail in contact_details))
                            )
                help_msgs.append(h_msg)
            if help_msgs:
                self.send_messages(help_msgs)
                logger.info("sent following message to help admins: %s" % help_msgs[0].text)
            else:
                logger.info("There are no help admins")



    def _mark_results_pending(self, results, connections):
        for connection in connections:
            self.waiting_for_pin[connection] = results
        for r in results:
            r.notification_status = 'notified'
            r.save()

    def results_avail_messages(self, clinic):
        results = self._pending_results(clinic)
        contacts = Contact.active.filter(location=clinic,
                                         types=const.get_clinic_worker_type())
        if not contacts:
            self.warning("No contacts registered to receiver results at %s! "
                         "These will go unreported until clinic staff "
                         "register at this clinic." % clinic)

        all_msgs = []
        for contact in contacts:
            msg = OutgoingMessage(connection=contact.default_connection,
                                  template=RESULTS_READY,
                                  name=contact.name, count=results.count())
            all_msgs.append(msg)

        return all_msgs, results

