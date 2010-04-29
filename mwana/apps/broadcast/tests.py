from rapidsms.contrib.handlers.app import App as handler_app
from rapidsms.contrib.locations.models import LocationType, Location
from rapidsms.models import Contact, Connection
from rapidsms.tests.scripted import TestScript
from mwana.const import get_clinic_worker_type, get_cba_type, get_zone_type

class TestApp(TestScript):
    apps = (handler_app,)
    
    def setUp(self):
        super(TestApp, self).setUp()
        type = LocationType.objects.create(singular="clinic", plural="clinics", 
                                           slug="clinics")
        clinic = Location.objects.create(type=type, name="demo", slug="demo") 
        clinic_zone= Location.objects.create(type=get_zone_type(), name="child", 
                                             slug="child", parent=clinic) 
        clinic_worker = self.create_contact(name="clinic_worker", location=clinic, 
                                            types=[get_clinic_worker_type()])
        clinic_worker2 = self.create_contact(name="clinic_worker2", location=clinic_zone,
                                             types=[get_clinic_worker_type()])
        cba = self.create_contact(name="cba", location=clinic,
                                  types=[get_cba_type()])
        cba2 = self.create_contact(name="cba2", location=clinic_zone,
                                   types=[get_cba_type()])
        
        self.all = [clinic_worker, clinic_worker2, cba, cba2]
        self.expected_keyword_to_groups = \
            {"ALL":    [clinic_worker, clinic_worker2, cba, cba2],
             "CLINIC": [clinic_worker, clinic_worker2],
             "CBA":    [cba, cba2]
             }
        
    def testGroupMessaging(self):
        self.startRouter()
        try:
            # test from each person so we know it works from all cases
            for contact in self.all:
                for keyword, recipients in self.expected_keyword_to_groups.items():
                    message_body = "what up fools!"
                    self.sendMessage(contact.default_connection.identity, "%s %s" %\
                                     (keyword, message_body))
                    messages = self.receiveAllMessages()
                    recipients_minus_self = [c for c in recipients if c != contact]
                    self.assertEqual(len(recipients_minus_self), len(messages), 
                                     ("message from %s went to correct amount of "
                                      "people for keyword %s. Expected %s but was "
                                      "%s") % (contact, keyword, len(recipients) - 1,
                                               len(messages)))
                    for msg in messages:
                        self.assertEqual("%(text)s [from %(from)s to %(keyword)s]" % \
                                         {"text": message_body, "from": contact.name,
                                          "keyword": keyword}, 
                                         msg.text)
                    msg_recipients = [msg.peer for msg in messages]
                    for responder in recipients_minus_self:
                        self.assertTrue(responder.default_connection.identity in msg_recipients)
                        # TODO: response workflow
                        
        finally:
            self.stopRouter()
    
    def create_contact(self, name, location, types):
        contact = Contact.objects.create(alias=name, name=name,
                                         location=location)
        contact.types = types
        script = "%(name)s > hello world" % {"name": name}
        self.runScript(script)
        connection = Connection.objects.get(identity=name)
        connection.contact = contact
        connection.save()
        return contact
        