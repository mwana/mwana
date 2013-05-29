# vim: ai ts=4 sts=4 et sw=4

from mwana import const
from mwana.apps.locations.models import Location
from mwana.apps.locations.models import LocationType
from rapidsms.models import Contact
from rapidsms.tests.scripted import TestScript
from mwana.apps.stringcleaning.inputcleaner import InputCleaner
from rapidsms.tests.scripted import TestScript


class TestApp(TestScript):
    
    ic = InputCleaner()
    def testSoundEx(self):
       self.assertEqual(self.ic.soundex('thri'), self.ic.soundex('three'))

    def testWordsToDigits(self):
        self.assertEqual(2, self.ic.words_to_digits('two'))
        self.assertEqual(2, self.ic.words_to_digits('too'))
        self.assertEqual(302, self.ic.words_to_digits('thri hundred two'))
        self.assertEqual(302, self.ic.words_to_digits('thri hundred and two'))
        self.assertEqual(26, self.ic.words_to_digits('twenti six'))
        self.assertEqual(8002, self.ic.words_to_digits('Eight thousand and two'))
        self.assertEqual(2001082, self.ic.words_to_digits('2 milion one thouzand Eighty too samples'))

    def testReplaceoilWith011(self):
        self.assertEqual('00111', self.ic.try_replace_oil_with_011('oOiIl'))
        self.assertEqual('403012', self.ic.try_replace_oil_with_011('4o3oi2'))


    def testRemoveDoubleSpaces(self):
        self.assertEqual('request 10 for db samples',
                         self.ic.remove_double_spaces('request  10    for  db      samples'))

    def testDigitToWord(self):
        self.assertEqual('One', self.ic.digit_to_word(1))
        self.assertEqual('Two', self.ic.digit_to_word(2))
        self.assertEqual('Thirty', self.ic.digit_to_word(30))
        self.assertEqual(None, self.ic.digit_to_word(31))

    def testLdistance(self):
        self.assertEqual(0, self.ic.ldistance('pea', 'PeA'))
        self.assertEqual(1, self.ic.ldistance('peac', 'PeA'))
        self.assertEqual(1, self.ic.ldistance('pea', 'PeAc'))
        self.assertEqual(1, self.ic.ldistance('pea', 'PeAc'))
        self.assertEqual(4, self.ic.ldistance('trev', 'nanc'))

    def testConditonalStringCleaning(self):
        """
        Tests string cleaning based on keywords
        """

        self.assertEqual(0, Contact.objects.count())
        ctr = LocationType.objects.create(slug=const.CLINIC_SLUGS[0])
        kdh = Location.objects.create(name="Kafue District Hospital",
                                      slug="kdh", type=ctr)
        Location.objects.create(name="Central Clinic",
                                                 slug="403012", type=ctr)

        #in JOIN clean separators including '/'
        script = """
        0979565992 > join 403012/jichael,mackson;1111
        0979565992 < Hi Jichael Mackson, thanks for registering for Results160 from Central Clinic. Your PIN is 1111. Reply with keyword 'HELP' if this is incorrect
        """
        self.runScript(script)

        #in AGENT clean separators including '/'
        script = """
        cba1 > agent 403012/2,peter;phiri
        cba1 < Thank you Peter Phiri! You have successfully registered as a RemindMi Agent for zone 2 of Central Clinic.
        cba2 > agent 403012/2,james;banda
        cba2 < Thank you James Banda! You have successfully registered as a RemindMi Agent for zone 2 of Central Clinic.
        """
        self.runScript(script)

        # in RESULT don't clean '/'
        script = """
        0979565992 > results 403012/10
        0979565992 < There are currently no results available for 403012/10. Please check if the SampleID is correct or sms HELP if you have been waiting for 2 months or more
        """
        self.runScript(script)

        # in broadcasts don't clean
        script = """
        cba1 > clinic 403012/10. Not 402012/09;
        0979565992 < 403012/10. Not 402012/09; [from Peter Phiri to CLINIC]
        cba1 > cba dont't filter , or / or ; or * or + or - in broadcasts
        cba2 < dont't filter , or / or ; or * or + or - in broadcasts [from Peter Phiri to CBA]
        """
        self.runScript(script)


        script = """
        0979565993 > join 403012/princess,obama;1111
        0979565993 < Hi Princess Obama, thanks for registering for Results160 from Central Clinic. Your PIN is 1111. Reply with keyword 'HELP' if this is incorrect
        """
        self.runScript(script)

        admin = Contact.active.get(connection__identity='0979565993')
        admin.is_help_admin = True
        admin.save()

        script = """
        0979565993 > blaster in blaster we dont clean , or / or ; or * or + or -
        0979565992 < in blaster we dont clean , or / or ; or * or + or - [from Princess Obama to Mwana Users]
        cba1 < in blaster we dont clean , or / or ; or * or + or - [from Princess Obama to Mwana Users]
        cba2 < in blaster we dont clean , or / or ; or * or + or - [from Princess Obama to Mwana Users]
        """
        self.runScript(script)

    def test_blank_message(self):
        script = """
        09795658992 >
        09795658992 < Sorry, I couldn't read your message. Make sure you have correct GSM message settings on your phone
        """

        self.runScript(script)

