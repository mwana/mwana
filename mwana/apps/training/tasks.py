# vim: ai ts=4 sts=4 et sw=4
import logging
import datetime
from celery import task
from threadless_router.router import Router
from mwana.apps.training.models import TrainingSession
from rapidsms.messages import OutgoingMessage
from rapidsms.models import Contact

logger = logging.getLogger(__name__)

DELAYED_TRAINING_TRAINER_MSG = "Hi %s, please send TRAINING STOP if you have stopped training for today at %s"
DELAYED_TRAINING_ADMIN_MSG = "A reminder was sent to %s, %s to state if training has ended for %s, %s"


@task
def send_endof_training_notification():

    logger.info('checking pending training sessions')
    pending_trainings = TrainingSession.objects.filter(is_on=True).exclude(
        trainer__is_active=False)

    for training in pending_trainings:
        if not training.trainer:
            training.is_on = False
            training.end_date = datetime.utcnow()
            training.save()
            msg = "Training has been stopped at %s: %s" % (
                training.location.name, training.location.slug)
            for help_admin in Contact.active.filter(is_help_admin=True):
                router = Router()
                if help_admin.default_connection is not None:
                    ha_msg = OutgoingMessage(
                        help_admin.default_connection, msg)
                    router.outgoing(ha_msg)

            continue

        if training.trainer.default_connection is not None:
            trainer_msg = OutgoingMessage(
                training.trainer.default_connection,
                DELAYED_TRAINING_TRAINER_MSG %
                (training.trainer.name, training.location.name))
            router.outgoing(trainer_msg)
        for help_admin in Contact.active.filter(is_help_admin=True):
            if help_admin.default_connection is not None:
                admin_msg = OutgoingMessage(
                    help_admin.default_connection,
                    DELAYED_TRAINING_ADMIN_MSG %
                    (training.trainer.name,
                     training.trainer.default_connection.identity,
                     training.location.name, training.location.slug))
                router.outgoing(admin_msg)
