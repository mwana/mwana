from datetime import datetime, timedelta

from rapidsms.models import Contact
from rapidsms.contrib.messagelog.models import Message

from mwana.apps.smgl.tests.shared import SMGLSetUp
from mwana.apps.smgl import const
from mwana.apps.smgl.reminders import send_inactive_notice



class SMGLReminderTest(SMGLSetUp):
    fixtures = ["initial_data.json"]

    def setUp(self):
        super(SMGLReminderTest, self).setUp()
        self.createDefaults()

    def testInactiveContactReminder(self):
        # get inbound messages for user
        da = Contact.objects.get(id=1)
        join_msg = Message.objects.get(direction="I", connection__contact=da)
        out_msgs = Message.objects.filter(direction="O", connection__contact=da)
        self.assertEqual(out_msgs.count(), 1)
        # this should do nothing because it's not in range
        send_inactive_notice(router_obj=self.router)
        self.assertEqual(out_msgs.count(), 1)

        # set the date back so it triggers a reminder
        now = datetime.utcnow().date()
        join_msg.date = now - timedelta(days=14)
        join_msg.save()
        send_inactive_notice(router_obj=self.router)
        out_msgs = Message.objects.filter(direction="O", connection__contact=da)
        self.assertEqual(out_msgs.count(), 2)
        self.assertEqual(out_msgs[1].text, const.INACTIVE_CONTACT)


