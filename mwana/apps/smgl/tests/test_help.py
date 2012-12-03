# vim: ai ts=4 sts=4 et sw=4
from rapidsms.models import Contact
from mwana.apps.smgl.tests.shared import SMGLSetUp
from mwana.apps.help.models import HelpRequest
from rapidsms.contrib.messagelog.models import Message



class HelpTest(SMGLSetUp):
    
    def setUp(self):
        super(HelpTest, self).setUp()
        self.createDefaults()
        HelpRequest.objects.all().delete()
        self.help_admin = self._make_admin("15")
        self.help_number = self.help_admin.default_connection.identity
        self.contact = Contact.active.get(connection__identity="11")

    def _make_admin(self, phone):
        help_admin = Contact.active.get(connection__identity=phone)
        help_admin.is_help_admin = True
        help_admin.save()
        return help_admin
    
    def testBasicHelpWorkflow(self):
        script = """
            11    > help me rhonda!
            11    < Sorry you're having trouble AntonTN. Your help request has been forwarded to a support team member and they will call you soon.
            {num} < AntonTN (tn) at Kalomo District has requested help. Please call them at 11 as soon as you can! Their message was: me rhonda!
        """.format(num=self.help_number)
        self.runScript(script)
        self.assertEqual(1, HelpRequest.objects.count())
        [req] = HelpRequest.objects.all()
        self.assertEqual(self.contact.default_connection, req.requested_by)
        self.assertEqual('me rhonda!', req.additional_text)
        self.assertEqual('P', req.status)
        
    def testUnregisteredHelpWorkflow(self):
        script = """
            90109 > help i need somebody!
            90109 < Sorry you're having trouble. Your help request has been forwarded to a support team member and they will call you soon.
            {num} < Someone has requested help. Please call them at 90109 as soon as you can! Their message was: i need somebody!
        """.format(num=self.help_number)
        self.runScript(script)
        self.assertEqual(1, HelpRequest.objects.count())
        [req] = HelpRequest.objects.all()
        self.assertEqual('90109', req.requested_by.identity)
        self.assertEqual('i need somebody!', req.additional_text)
        self.assertEqual('P', req.status)
        
    def testMultipleAdmins(self):
        other_admin_num = "14"
        self._make_admin(other_admin_num)
        script = """
            11    > help lessness blues
            11    < Sorry you're having trouble AntonTN. Your help request has been forwarded to a support team member and they will call you soon.
            {num} < AntonTN (tn) at Kalomo District has requested help. Please call them at 11 as soon as you can! Their message was: lessness blues
            {oth} < AntonTN (tn) at Kalomo District has requested help. Please call them at 11 as soon as you can! Their message was: lessness blues
        """.format(num=self.help_number, oth=other_admin_num)
        self.runScript(script)
        self.assertEqual(1, HelpRequest.objects.count())

    def testDeregister(self):
        prev_count = Message.objects.filter(connection__identity=self.help_number).count()
        self.help_admin.is_help_admin = False
        self.help_admin.save()
        script = """
            90109 > help
            90109 < Sorry you're having trouble. Your help request has been forwarded to a support team member and they will call you soon.
        """.format(num=self.help_number)
        self.runScript(script)
        self.assertEqual(1, HelpRequest.objects.count())
        self.assertEqual(prev_count,
                         Message.objects.filter(connection__identity=self.help_number).count())
        