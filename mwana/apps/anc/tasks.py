# vim: ai ts=4 sts=4 et sw=4

import logging

from rapidsms.messages.outgoing import OutgoingMessage

from mwana.apps.anc.models import SentCHWMessage
from mwana.apps.anc.models import Client
from mwana.apps.anc.models import EducationalMessage
from mwana.apps.anc.models import SentClientMessage

_ = lambda s: s

logger = logging.getLogger('mwana.apps.anc.tasks')


def send_anc_messages(router):
    logger.info('Sending anc messages')

    for client in Client.objects.filter(is_active=True, phone_confirmed=True):
        if not client.is_eligible_for_messages():
            continue
        age = client.get_gestational_age()
        educational_msgs = EducationalMessage.objects.filter(gestational_age=age)
        if not educational_msgs:
            continue
        for ed in educational_msgs:
            if SentClientMessage.objects.filter(client=client, message=ed).exists():
                continue
            OutgoingMessage(client.connection, ed.text).send()
            SentClientMessage.objects.create(client=client, message=ed)

    for client in Client.objects.exclude(community_worker=None):
        if not client.is_eligible_for_messages_by_pregnancy_status():
            continue
        age = client.get_gestational_age()
        educational_msgs = EducationalMessage.objects.filter(gestational_age=age)
        if not educational_msgs:
            continue
        for ed in educational_msgs:
            if SentCHWMessage.objects.filter(community_worker=client.community_worker, message=ed).exists():
                continue
            chw_msg = ed.text.replace(' Stop messages with 5555', '')
            OutgoingMessage(client.community_worker.connection, "%s: %s" % (client.connection.identity, chw_msg)).send()
            SentCHWMessage.objects.create(community_worker=client.community_worker, message=ed)
