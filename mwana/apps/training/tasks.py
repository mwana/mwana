# vim: ai ts=4 sts=4 et sw=4
import logging
from mwana.apps.training.models import TrainingSession
from rapidsms.messages import OutgoingMessage
from rapidsms.models import Contact

logger = logging.getLogger(__name__)

DELAYED_TRAINING_TRAINER_MSG = "Hi %s, please send TRAINING STOP if you have stopped training for today at %s"
DELAYED_TRAINING_ADMIN_MSG = "A reminder was sent to %s, %s to state if training has ended for %s, %s"

def send_endof_training_notification(router):

    logger.info('checking pending training sessions')
    pending_trainings = TrainingSession.objects.filter(is_on=True).exclude(trainer__is_active=False)

    for training in pending_trainings:
        OutgoingMessage(training.trainer.default_connection,
                        DELAYED_TRAINING_TRAINER_MSG %
                        (training.trainer.name, training.location.name)
                        ).send()
        for help_admin in Contact.active.filter(is_help_admin=True):
            OutgoingMessage(help_admin.default_connection,
                            DELAYED_TRAINING_ADMIN_MSG %
                            (training.trainer.name,
                            training.trainer.default_connection.identity,
                            training.location.name, training.location.slug)
                            ).send()


