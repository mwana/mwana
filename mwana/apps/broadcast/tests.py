# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.locations.models import LocationType, Location
from rapidsms.models import Contact, Connection
from rapidsms.tests.scripted import TestScript
from mwana import const 
from mwana.settings_project import DEFAULT_RESPONSE
from mwana.apps.labresults.messages import CLINIC_DEFAULT_RESPONSE, CBA_DEFAULT_RESPONSE
from mwana.apps.broadcast.models import BroadcastMessage, BroadcastResponse
import mwana.const as const
import time
from mwana.const import (get_province_worker_type, get_clinic_worker_type,
get_cba_type, get_hub_worker_type, get_district_worker_type)

class TestApp(TestScript):

    def setUp(self):
        super(TestApp, self).setUp()
        clinic_type, _ = LocationType.objects.get_or_create(singular="clinic",
                                                     plural="clinics",
                                                     slug="clinics")
        district_type, _ = LocationType.objects.get_or_create(singular="district",
                                                     plural="districts",
                                                     slug="districts")
        province_type, _ = LocationType.objects.get_or_create(singular="province",
                                                     plural="provinces",
                                                     slug="provinces")
        self.province = Location.objects.create(type=province_type, name="Luapula", slug="400000")
        self.district = Location.objects.create(type=district_type, name="Mansa", slug="403000")
        self.district.parent=self.province
        self.district.save()
        self.district2 = Location.objects.create(type=district_type, name="Kawambwa", slug="402000")
        self.district2.parent=self.province
        self.district2.save()
        self.clinic = Location.objects.create(type=clinic_type, name="Central Clinic", slug="403020")
        self.clinic.parent = self.district
        self.clinic.save()
        self.clinic2 = Location.objects.create(type=clinic_type, name="Other Clinic", slug="402020")
        self.clinic2.parent = self.district2
        self.clinic2.save()
        zone_type = LocationType.objects.create(slug=const.ZONE_SLUGS[0])

        self.clinic_zone= Location.objects.create(type=zone_type, name="2",
                                                   slug="2", parent=self.clinic)
        clinic_worker = self.create_contact(name="clinic_worker", location=self.clinic,
                                            types=[get_clinic_worker_type()])
        clinic_worker2 = self.create_contact(name="clinic_worker2", location=self.clinic,
                                             types=[get_clinic_worker_type()])



        cba = self.create_contact(name="cba", location=self.clinic_zone,
                                  types=[get_cba_type()])
        cba2 = self.create_contact(name="cba2", location=self.clinic_zone,
                                   types=[get_cba_type()])
        
        self.all = [clinic_worker, clinic_worker2, cba, cba2]
        self.expected_keyword_to_groups = \
            {"ALL":    [clinic_worker, clinic_worker2, cba, cba2],
             "CLINIC": [clinic_worker, clinic_worker2],
             "CBA":    [cba, cba2],
             }


    def create_msg_workers(self):
        dho = self.create_contact(name="dho", location=self.district,
                                            types=[get_district_worker_type()])
        dho2 = self.create_contact(name="dho2", location=self.district,
                                            types=[get_district_worker_type()])

        # control contacts
        pho = self.create_contact(name="pho", location=self.province,
                                            types=[get_province_worker_type()])
        dho3 = self.create_contact(name="dho3", location=self.district2,
                                            types=[get_district_worker_type()])
        clinic_worker3 = self.create_contact(name="clinic_worker3", location=self.clinic2,
                                             types=[get_clinic_worker_type()])
        hub_worker = self.create_contact(name="hub_worker", location=self.clinic,
                                             types=[get_hub_worker_type()])
    def testIgnoringExtraneousPunctuation(self):

        self.create_msg_workers()

        script="""
        dho_number > msg dho. hello sir
        dho2_number < hello sir [from dho (dho_number) of Mansa to DHO]
        """
        self.runScript(script)

        script="""
        cba_number > msg cba, hello sir
        cba2_number < hello sir [from cba (cba_number) of Central Clinic: Zone 2 to CBA]
        """
        self.runScript(script)
        
    def testMsgByDho(self):

        self.create_msg_workers()

        script="""
        dho_number > msg my own way
        dho_number < Sorry, I din't understand that. To send a message SEND: MSG <GROUP> <your message>. The groups you can send to are: DHO, CLINIC, ALL
        dho_number > msg
        dho_number < To send a message SEND: MSG <GROUP> <your message>. The groups you can send to are: DHO, CLINIC, ALL
        dho_number > msg cba come and get sweets
        dho_number < 'CBA' is not a valid message group for you. To send a message SEND: MSG <GROUP> <your message>. The groups you can send to are: DHO, CLINIC, ALL
        """
        self.runScript(script)

        script="""
        dho_number > msg all testing dho blasting
        """
        self.runScript(script)

        msgs=self.receiveAllMessages()
        response = [msg for msg in msgs if (msg.connection.identity == 'dho_number' and \
                                             msg.text == "Your message has been sent to 3 people")]
        self.assertEqual(len(response), 1, msgs)

        self.assertEqual(4, len(msgs), msgs)
        expected_recipients = ["dho2", "clinic_worker", "clinic_worker2"]
        actual_recipients = []

        for msg in filter(lambda x:x not in response, msgs):
            self.assertEqual(msg.text,"testing dho blasting [from dho (dho_number) of Mansa to ALL]")
            actual_recipients.append(msg.contact.name)
        difference = list(set(actual_recipients).difference(set(expected_recipients)))
        self.assertEqual([], difference)

        script="""
        dho_number > msg dho testing dho blasting
        """

        self.runScript(script)
        msgs=self.receiveAllMessages()

        # no extra msgs sent
        self.assertEqual(2, len(msgs))
        self.assertEqual('dho2', filter(lambda msg: not msg.text.startswith("Your messages has been sent"), msgs)[0].contact.name)
        self.assertEqual(msgs[0].text, 'testing dho blasting [from dho (dho_number) of Mansa to DHO]')

        script="""
        dho_number > msg clinic testing dho blasting
        """

        self.runScript(script)
        msgs=self.receiveAllMessages()
        response = [msg for msg in msgs if (msg.connection.identity == 'dho_number' and \
                                             msg.text == "Your message has been sent to 2 people")]
        self.assertEqual(len(response), 1, msgs)

        self.assertEqual(3,len(msgs))
        expected_recipients = ["clinic_worker", "clinic_worker2"]
        actual_recipients = []

        for msg in filter(lambda x:x not in response, msgs):
            self.assertEqual(msg.text, "testing dho blasting [from dho (dho_number) of Mansa to CLINIC]")
            actual_recipients.append(msg.contact.name)
        difference = list(set(actual_recipients).difference(set(expected_recipients)))
        self.assertEqual([], difference)

    def testMsgByClinicWorker(self):

        self.create_msg_workers()
       
        script="""
        clinic_worker_number > msg my own way
        clinic_worker_number < Sorry, I din't understand that. To send a message SEND: MSG <GROUP> <your message>. The groups you can send to are: CBA, CLINIC, ALL, DHO
        clinic_worker_number > msg
        clinic_worker_number < To send a message SEND: MSG <GROUP> <your message>. The groups you can send to are: CBA, CLINIC, ALL, DHO
        """
        self.runScript(script)

        script="""
        clinic_worker_number > msg ALL testing msg all
        """
        self.runScript(script)

        msgs=self.receiveAllMessages()
        response = [msg for msg in msgs if (msg.connection.identity == 'clinic_worker_number' and\
             msg.text == "Your message has been sent to 3 people")]
        self.assertEqual(len(response), 1)

        self.assertEqual(4, len(msgs))
        expected_recipients = ["cba", "cba2", "clinic_worker2"]
        actual_recipients = []

        for msg in filter(lambda x:x not in response, msgs):
            self.assertEqual(msg.text,"testing msg all [from clinic_worker (clinic_worker_number) of Central Clinic to ALL]")
            actual_recipients.append(msg.contact.name)
        difference = list(set(actual_recipients).difference(set(expected_recipients)))
        self.assertEqual([], difference)

        script="""
        clinic_worker_number > msg clinic sending from clinic_worker to clinic
        """

        self.runScript(script)
        msgs=self.receiveAllMessages()

        # no extra msgs sent
        self.assertEqual(2, len(msgs))
        self.assertEqual('clinic_worker2', filter(lambda msg: not msg.text.startswith("Your messages has been sent"), msgs)[0].contact.name)
        self.assertEqual(msgs[0].text, 'sending from clinic_worker to clinic [from clinic_worker (clinic_worker_number) of Central Clinic to CLINIC]')

        script="""
        clinic_worker_number > msg cba testing clinic to cba
        """

        self.runScript(script)
        msgs=self.receiveAllMessages()
        response = [msg for msg in msgs if (msg.connection.identity == 'clinic_worker_number' and\
             msg.text == "Your message has been sent to 2 people")]
        self.assertEqual(len(response), 1)

        self.assertEqual(3, len(msgs))
        expected_recipients = ["cba", "cba2"]
        actual_recipients = []

        for msg in filter(lambda x:x not in response, msgs):
            self.assertEqual(msg.text, "testing clinic to cba [from clinic_worker (clinic_worker_number) of Central Clinic to CBA]")
            actual_recipients.append(msg.contact.name)
        difference = list(set(actual_recipients).difference(set(expected_recipients)))
        self.assertEqual([], difference)

        script="""
        clinic_worker_number > msg dho testing clinic to dho
        """

        self.runScript(script)
        msgs=self.receiveAllMessages()
        response = [msg for msg in msgs if (msg.connection.identity == 'clinic_worker_number' and\
             msg.text == "Your message has been sent to 2 people")]
        self.assertEqual(len(response), 1)
        
        self.assertEqual(3,len(msgs), msgs)
        expected_recipients = ["dho", "dho2"]
        actual_recipients = []

        for msg in filter(lambda x:x not in response, msgs):
            self.assertEqual(msg.text, "testing clinic to dho [from clinic_worker (clinic_worker_number) of Central Clinic to DHO]")
            actual_recipients.append(msg.contact.name)
        difference = list(set(actual_recipients).difference(set(expected_recipients)))
        self.assertEqual([], difference)

    def testMsgByCba(self):

        self.create_msg_workers()

        script="""
        cba_number > msg my own way
        cba_number < Sorry, I din't understand that. To send a message SEND: MSG <GROUP> <your message>. The groups you can send to are: CBA, CLINIC, ALL
        cba_number > msg
        cba_number < To send a message SEND: MSG <GROUP> <your message>. The groups you can send to are: CBA, CLINIC, ALL
        cba_number > msg dho come and get sweets
        cba_number < 'DHO' is not a valid message group for you. To send a message SEND: MSG <GROUP> <your message>. The groups you can send to are: CBA, CLINIC, ALL
        """
        self.runScript(script)

        script="""
        cba_number > msg all testing msg all
        """
        self.runScript(script)

        msgs=self.receiveAllMessages()
        response = [msg for msg in msgs if (msg.connection.identity == 'cba_number' and\
             msg.text == "Your message has been sent to 3 people")]
        self.assertEqual(len(response), 1)

        self.assertEqual(4,len(msgs))
        expected_recipients = ["cba2", "clinic_worker", "clinic_worker2"]
        actual_recipients = []

        for msg in filter(lambda x:x not in response, msgs):
            self.assertEqual(msg.text,"testing msg all [from cba (cba_number) of Central Clinic: Zone 2 to ALL]")
            actual_recipients.append(msg.contact.name)
        difference = list(set(actual_recipients).difference(set(expected_recipients)))
        self.assertEqual([], difference)

        script="""
        cba_number > msg cba sending from cbc to cba
        """

        self.runScript(script)
        msgs=self.receiveAllMessages()

        # no extra msgs sent
        self.assertEqual(2, len(msgs))
        self.assertEqual('cba2', filter(lambda msg: not msg.text.startswith("Your messages has been sent"), msgs)[0].contact.name)
        self.assertEqual(msgs[0].text, 'sending from cbc to cba [from cba (cba_number) of Central Clinic: Zone 2 to CBA]')

        script="""
        cba_number > msg clinic testing cba to clinic
        """

        self.runScript(script)
        msgs=self.receiveAllMessages()
        response = [msg for msg in msgs if (msg.connection.identity == 'cba_number' and\
             msg.text == "Your message has been sent to 2 people")]
        self.assertEqual(len(response), 1)

        self.assertEqual(3, len(msgs))
        expected_recipients = ["clinic_worker", "clinic_worker2"]
        actual_recipients = []

        for msg in filter(lambda x:x not in response, msgs):
            self.assertEqual(msg.text, "testing cba to clinic [from cba (cba_number) of Central Clinic: Zone 2 to CLINIC]")
            actual_recipients.append(msg.contact.name)
        difference = list(set(actual_recipients).difference(set(expected_recipients)))
        self.assertEqual([], difference)


    def testGroupMessaging(self):
        self.assertEqual(0, BroadcastMessage.objects.count())
        self.assertEqual(0, BroadcastResponse.objects.count())
        running_count = 0
        self.startRouter()
        try:
            # test from each person so we know it works from all cases
            for contact in self.all:
                for keyword, recipients in self.expected_keyword_to_groups.items():
                    running_count += 1
                    message_body = "what's up people!"
                    response = "not much G!"
                    self.sendMessage(contact.default_connection.identity, "%s %s" %\
                                     (keyword, message_body))
                    messages = self.receiveAllMessages()
                    recipients_minus_self = [c for c in recipients if c != contact]
                    self.assertEqual(len(recipients_minus_self), len(messages),
                                     ("message from %s went to incorrect amount of "
                                      "people for keyword %s. Expected %s but was "
                                      "%s") % (contact, keyword, len(recipients) - 1,
                                               len(messages)))
                    for msg in messages:#from clinic_worker (clinic_worker_number) of Central Clinic to ALL
                        self.assertEqual("%(text)s [from %(from)s to %(keyword)s]" % \
                                         {"text": message_body,
                                         "from": "%s (%s) of %s" % (
                                         contact.name,
                                         contact.default_connection.identity,
                                         contact.location),
                                          "keyword": keyword},
                                         msg.text)

                    # check DB objects
                    self.assertEqual(running_count, BroadcastMessage.objects.count())
                    last_msg = BroadcastMessage.objects.order_by("-date")[0]
                    self.assertEqual(contact, last_msg.contact)
                    self.assertEqual(keyword, last_msg.group)
                    self.assertEqual(message_body, last_msg.text)
                    for responder in recipients_minus_self:
                        self.assertTrue(responder in last_msg.recipients.all(),
                                        "Recipient %s was linked in the db" % responder)

                    msg_recipients = [msg.peer for msg in messages]
                    for responder in recipients_minus_self:
                        self.assertTrue(responder.default_connection.identity in msg_recipients)

                        # response workflow
                        self.sendMessage(responder.default_connection.identity, response)
                        responses = self.receiveAllMessages()
                        self.assertEqual(1, len(responses))
                        self.assertEqual(responder.default_connection.identity, responses[0].peer)
                        default_responces = [DEFAULT_RESPONSE, CLINIC_DEFAULT_RESPONSE, CBA_DEFAULT_RESPONSE]
                        self.assertTrue(responses[0].text in default_responces)
                        # As per http://groups.google.com/group/mwana/tree/browse_frm/thread/07f5d6599ac91832/695178783cf65e76
                        # No longer supporting broadcast responses.
                        self.assertEqual(0, BroadcastResponse.objects.count())

        finally:
            self.stopRouter()

    def create_contact(self, name, location, types):
        contact = Contact.objects.create(alias=name, name=name,
                                         location=location)
        contact.types = types
        script = "%(name)s_number > hello world" % {"name": name}
        self.runScript(script)
        connection = Connection.objects.get(identity=name + '_number')
        connection.contact = contact
        connection.save()
        return contact
    
    def testBlaster(self):
        script = "help_admin_number > hello world"
        self.runScript(script)
        connection = Connection.objects.get(identity="help_admin_number")
        help_admin = Contact.objects.create(alias='help_admin', is_active = True, name="help_admin",
                                         location=self.clinic, is_help_admin = True)
        help_admin.types.add(const.get_clinic_worker_type())
                                
        connection.contact = help_admin
        connection.save()
        time.sleep(1)
        script = """
            help_admin_number > blast hello
            clinic_worker_number < hello [from help_admin (help_admin_number) of Central Clinic to Mwana Users]
            clinic_worker2_number < hello [from help_admin (help_admin_number) of Central Clinic to Mwana Users]
            cba_number < hello [from help_admin (help_admin_number) of Central Clinic to Mwana Users]
            cba2_number < hello [from help_admin (help_admin_number) of Central Clinic to Mwana Users]
        """
        self.runScript(script)
        