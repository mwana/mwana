from rapidsms.contrib.handlers.app import App as handler_app
from rapidsms.models import Contact
from mwana.apps.patienttracing.models import PatientTrace
from rapidsms.tests.scripted import TestScript
from mwana.apps.locations.models import Location, LocationType

from mwana.apps.reminders.app import App
from mwana.apps.reminders import models as reminders
from mwana import const

import time
import json

import datetime
import mwana.const as const
from django.contrib.auth.models import Permission
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from mwana.apps.labresults import models as labresults
from mwana.apps.labresults.mocking import get_fake_results
from mwana.apps.labresults.models import Result, SampleNotification
from mwana.apps.locations.models import Location
from mwana.apps.locations.models import LocationType
from rapidsms.models import Connection
from rapidsms.models import Contact
from rapidsms.tests.scripted import TestScript
from mwana.apps.labresults import tasks
from mwana.util import is_today_a_weekend, is_weekend
from mwana.apps.labresults.testdata.payloads import INITIAL_PAYLOAD, CHANGED_PAYLOAD
from mwana.apps.labresults.testdata.reports import *

from rapidsms.models import Contact

class TestApp(TestScript):
    def setUp(self):
        # this call is required if you want to override setUp
        super(TestApp, self).setUp()
        self.type = LocationType.objects.get_or_create(singular="clinic", plural="clinics", slug=const.CLINIC_SLUGS[2])[0]
        self.type1 = LocationType.objects.get_or_create(singular="district", plural="districts", slug="districts")[0]        
        self.type2 = LocationType.objects.get_or_create(singular="province", plural="provinces", slug="provinces")[0]        
        self.luapula = Location.objects.create(type=self.type2, name="Luapula Province", slug="luapula")
        self.mansa = Location.objects.create(type=self.type1, name="Mansa District", slug="mansa", parent = self.luapula)
        self.samfya = Location.objects.create(type=self.type1, name="Samfya District", slug="samfya", parent = self.luapula)
        self.clinic = Location.objects.create(type=self.type, name="Mibenge Clinic", slug="402029", parent = self.samfya)
        self.mansa_central = Location.objects.create(type=self.type, name="Central Clinic", slug="403012", parent = self.mansa)

        
        self.support_clinic = Location.objects.create(type=self.type, name="Support Clinic", slug="spt")
        
        #create a clinic worker
        script = "clinic_worker > hello world"
        self.runScript(script)
        connection = Connection.objects.get(identity="clinic_worker")
        
        self.contact = Contact.objects.create(alias="banda", name="John Banda", 
                                              location=self.clinic, pin="4567")
        self.contact.types.add(const.get_clinic_worker_type())
                                
        connection.contact = self.contact
        connection.save()
        
        # create another one
        self.other_contact = Contact.objects.create(alias="mary", name="Mary Phiri", 
                                                    location=self.clinic, pin="6789")
        self.other_contact.types.add(const.get_clinic_worker_type())
        
        Connection.objects.create(identity="other_worker", backend=connection.backend, 
                                  contact=self.other_contact)
        connection.save()


        # create CBA staff
        self.cba_contact = Contact.objects.create(alias="cba1", name="Cba One",
                                                    location=self.clinic, pin="1111", is_help_admin=False)
        self.cba_contact.types.add(const.get_cba_type())

        Connection.objects.create(identity="cba_contact", backend=connection.backend,
                                  contact=self.cba_contact)
        connection.save()
        
        PatientTrace

    
    def testMaualTrace(self):
        self.assertEqual(0, PatientTrace.objects.count())

        script = """
            lost   > trace
            lost   < Sorry, the system could not understand your message. To trace a patient please send: TRACE <PATIENT_NAME>
            clinic_worker     > trace mary
            cba_contact       < Hello Cba One, please find mary and tell them to come to the clinic. When you've told them, please reply to this msg with: TOLD mary
            clinic_worker     < Thank You John Banda! Your patient trace has been initiated.  You will be notified when the patient is found.
            cba_contact       > TOLD MARY
        """
        self.runScript(script)
