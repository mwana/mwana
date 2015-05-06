# vim: ai ts=4 sts=4 et sw=4
from __future__ import absolute_import
import logging
import datetime
from celery import shared_task
from mwana.apps.training.models import TrainingSession
from rapidsms.models import Contact
from rapidsms.router import send

logger = logging.getLogger(__name__)

DELAYED_TRAINING_TRAINER_MSG = """Hi %s, please send TRAINING STOP if you have
stopped training for today at %s"""
DELAYED_TRAINING_ADMIN_MSG = """A reminder was sent to %s, %s to state if
training has ended for %s, %s"""


@shared_task
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
                # router = Router()
                if help_admin.default_connection is not None:
                    send(msg, [help_admin.default_connection])

        trainer_msg = DELAYED_TRAINING_TRAINER_MSG % (training.trainer.name,
                                                      training.location.name)
        if training.trainer.default_connection is not None:
            send(trainer_msg, [training.trainer.default_connection])

            admin_msg = DELAYED_TRAINING_ADMIN_MSG % (
                training.trainer.name,
                training.trainer.default_connection.identity,
                training.location.name, training.location.slug)
            for help_admin in Contact.active.filter(is_help_admin=True):
                if help_admin.default_connection is not None:
                    send(admin_msg, [help_admin.default_connection])
