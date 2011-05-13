import datetime
import time

from django.test import TestCase

from rapidsms.tests.scripted import TestScript
from rapidsms.models import Connection

from mwana.apps.tlcprinters.models import MessageConfirmation
from mwana.apps.tlcprinters.messages import TLCOutgoingMessage


class TLCTest(TestScript):

    def setUp(self):
        super(TLCTest, self).setUp()
        # this gets the backend and connection in the db
        self.runScript("tester > hello world 123")
        self.tester = Connection.objects.get(identity='tester')

    def test_confirm(self):
        mc = MessageConfirmation.objects.create(connection=self.tester,
                                               sent_at=datetime.datetime.now(),
                                               text='abc', seq_num=255,
                                               confirmed=False)
        time.sleep(0.1)
        self.startRouter()
        self.sendMessage('tester', 'Confirm SMS: FF')
        responses = self.receiveAllMessages()
        self.stopRouter()
        self.assertEqual(len(responses), 0, 'Unexpected message(s) received: '
                         + str(responses))
        mc = MessageConfirmation.objects.get(pk=mc.pk)
        self.assertTrue(mc.confirmed)

    def test_tlc_outgoing_msg(self):
        time.sleep(0.1)
        self.startRouter()
        msg = TLCOutgoingMessage(self.tester, 'hello printer')
        msg.send()
        self.stopRouter()
        self.assertTrue(msg.sent)
        msg_conf = MessageConfirmation.objects.get()
        self.assertEqual(msg_conf.text, '00hello printer')
        self.assertEqual(msg_conf.seq_num, 0)
        self.assertFalse(msg_conf.confirmed)
