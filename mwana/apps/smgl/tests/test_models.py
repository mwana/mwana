from mwana.apps.smgl.tests.shared import SMGLSetUp
from rapidsms.models import Contact


class SMGLContactTest(SMGLSetUp):

    fixtures = ["initial_data.json"]

    def setUp(self):
        super(SMGLContactTest, self).setUp()
        self.createDefaults()

    def testUserWithDistrictLocation(self):
        """ Returns the district directly associated with the Contact"""
        contact = Contact.objects.get(name="AntonTN")
        self.assertEqual(contact.location, contact.get_current_district())

    def testUserWithLocation(self):
        """ Returns the district indirectly associated with the Contact"""
        contact = Contact.objects.get(name="AntonDA")
        district = contact.get_current_district()
        self.assertNotEqual(contact.location, district)
        self.assertEqual('district', district.type.singular)
