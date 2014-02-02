from datetime import datetime, timedelta

from rapidsms.models import Contact
from rapidsms.contrib.messagelog.models import Message

from mwana.apps.contactsplus.models import ContactType

from mwana.apps.smgl.tests.shared import SMGLSetUp, create_mother
from mwana.apps.smgl import const
from mwana.apps.smgl.reminders import (send_inactive_notice_cbas,
    send_inactive_notice_data_clerks,
    send_expected_deliveries)


class SMGLReminderTest(SMGLSetUp):
    fixtures = ["initial_data.json"]

    def setUp(self):
        super(SMGLReminderTest, self).setUp()
        self.createDefaults()
        self.now = datetime.utcnow().date()
        self.mom = create_mother(data={'edd': self.now + timedelta(days=5)})
        self.incharge = ContactType.objects.get(slug='incharge')
        self.anton = Contact.objects.get(name='antonOther')
        self.anton.types.add(self.incharge)
        self.anton.location = self.mom.location
        self.anton.save()

    def testInactiveContactReminderDataClerks(self):
        # get inbound messages for user
        da = Contact.objects.get(id=5)#5 is a data clerk
        join_msg = Message.objects.get(direction="I", connection__contact=da)
        out_msgs = Message.objects.filter(direction="O", connection__contact=da)
        self.assertEqual(out_msgs.count(), 1)
        # this should do nothing because it's not in range
        send_inactive_notice_data_clerks(router_obj=self.router)
        self.assertEqual(out_msgs.count(), 1)
        # set the date back so it triggers a reminder
        join_msg.date = self.now - timedelta(days=14)
        join_msg.save()
        send_inactive_notice_data_clerks(router_obj=self.router)
        out_msgs = Message.objects.filter(direction="O", connection__contact=da)
        self.assertEqual(out_msgs.count(), 2)
        self.assertEqual(out_msgs[1].text, const.INACTIVE_CONTACT%{'days':14})

    def testExpectedEddReminder(self):
        Message.objects.all().delete()

        # this should send 1 msg with 1 count
        send_expected_deliveries(router_obj=self.router)
        msgs = Message.objects.all()
        self.assertEqual(msgs.count(), 1)
        self.assertEqual(msgs[0].text, const.EXPECTED_EDDS % {'edd_count': 1})

    def testExpectedEddReminderBeforeRange(self):
        Message.objects.all().delete()

        # this should send 0 as it's out of date range (less than)
        self.mom.edd = self.now - timedelta(days=1)
        self.mom.save()
        send_expected_deliveries(router_obj=self.router)
        msgs = Message.objects.all()
        self.assertEqual(msgs.count(), 0)

    def testExpectedEddReminderAfterRange(self):
        Message.objects.all().delete()

        # this should send 0 as it's out of date range (greater than)
        self.mom.edd = self.now + timedelta(days=8)
        self.mom.save()
        send_expected_deliveries(router_obj=self.router)
        msgs = Message.objects.all()
        self.assertEqual(msgs.count(), 0)

    def testExpectedEddNoInChargeReminder(self):
        Message.objects.all().delete()
        self.anton.types.clear()

        # this should do nothing because there's no incharge
        send_expected_deliveries(router_obj=self.router)
        self.assertEqual(Message.objects.all().count(), 0)


