from rapidsms.contrib.locations.models import LocationType, Location
from rapidsms.models import Contact
from django.test.testcases import TestCase

class TestContactsPlus(TestCase):
    
    def testParentChildLocations(self):
        type = LocationType.objects.create(singular="test", plural="tests", slug="tests")
        parent = Location.objects.create(type=type, name="parent", slug="parent") 
        child1 = Location.objects.create(type=type, name="child1", slug="child1", parent=parent) 
        child2 = Location.objects.create(type=type, name="child2", slug="child2", parent=parent) 
        grandchild = Location.objects.create(type=type, name="grandchild", slug="grandchild", parent=child1) 
        orphan = Location.objects.create(type=type, name="orphan", slug="orphan")
        
        
        contact1 = Contact.objects.create(name="contact1", location=parent)
        contact2 = Contact.objects.create(name="contact2", location=child1)
        contact3 = Contact.objects.create(name="contact3", location=child2)
        contact4 = Contact.objects.create(name="contact4", location=grandchild)
        contact5 = Contact.objects.create(name="contact5")
        
        self.assertEqual(5, Location.objects.count())
        self.assertEqual(5, Contact.objects.count())
        self.assertEqual(3, Contact.objects.location(parent).count())
        Contact.objects.location(parent).get(id=contact1.id)
        Contact.objects.location(parent).get(id=contact2.id)
        Contact.objects.location(parent).get(id=contact3.id)
        
        self.assertEqual(2, Contact.objects.location(child1).count())
        Contact.objects.location(child1).get(id=contact2.id)
        Contact.objects.location(child1).get(id=contact4.id)
        
        self.assertEqual(1, Contact.objects.location(child2).count())
        Contact.objects.location(child2).get(id=contact3.id)
        
        self.assertEqual(1, Contact.objects.location(grandchild).count())
        Contact.objects.location(grandchild).get(id=contact4.id)
        
        self.assertEqual(0, Contact.objects.location(orphan).count())
        
        
        
    def testActiveContacts(self):
        contact1 = Contact.objects.create(name="contact1", is_active=True)
        contact2 = Contact.objects.create(name="contact2", is_active=True)
        contact3 = Contact.objects.create(name="contact3", is_active=False)
        
        self.assertEqual(3, Contact.objects.count())
        self.assertEqual(2, Contact.active.count())
        
        for contact in [contact1, contact2]:
            Contact.objects.get(id=contact.id)
            Contact.active.get(id=contact.id)
        
        Contact.objects.get(id=contact3.id)
        try:
            Contact.active.get(id=contact3.id)
            self.fail("Should have found an inactive contact in Contacts.active")
        except:
            pass
