# vim: ai ts=4 sts=4 et sw=4

import logging

from rapidsms.messages.outgoing import OutgoingMessage

from mwana.apps.anc.models import Client
from mwana.apps.anc.models import EducationalMessage
from mwana.apps.anc.models import SentMessage

_ = lambda s: s


logger = logging.getLogger('mwana.apps.anc.tasks')


def send_anc_messages(router):
    logger.info('Sending anc messages')

    for client in Client.objects.filter(is_active=True):
        if not client.is_eligible_for_messages():
            continue
        age = client.get_gestational_age()
        educational_msgs = EducationalMessage.objects.filter(gestational_age=age)
        if not educational_msgs:
            continue
        for ed in educational_msgs:
            if SentMessage.objects.filter(client=client, message=ed).exists():
                continue
            OutgoingMessage(client.connection, ed.text).send()
            SentMessage.objects.create(client=client, message=ed)
