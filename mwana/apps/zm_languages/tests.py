# vim: ai ts=4 sts=4 et sw=4

from datetime import date
from mwana.apps.translator.models import Dictionary
from mwana.apps.translator.models import Language
from mwana import const
from mwana.apps.locations.models import Location
from mwana.apps.locations.models import LocationType
from mwana.apps.reminders import models as reminders
from datetime import timedelta
from rapidsms.tests.scripted import TestScript

MESSAGES = '''
join cba {language} 502012  2 Michael Kaseba
BIRTH 4/3/2010 laura
BIRTH h 4/3/2010 laura
BIRTH f 4/3/2010 laura
rmdemo 502012
told patient 1
confirm patient 2
HELP
UNKNOWN
BIRTH f 4/3/2040 laura
BIRTH f 44/3/2040 laura
mwana
mwana 777
'''

class LangaugeSetup(TestScript):
    def setUp(self):
        # this call is required if you want to override setUp
        super(LangaugeSetup, self).setUp()
        location_type = LocationType.objects.create(slug=const.CLINIC_SLUGS[0])
        Location.objects.create(name="Kafue District Hospital", slug="502012",
                                type=location_type)
        reminders.Event.objects.create(name="Birth", slug="birth", gender='f')
        reminders.Event.objects.create(name="Birth", slug="mwana", gender='f')
        
        bemba = Language.objects.create(slug='bem', name='Bemba')
        lozi = Language.objects.create(slug='loz', name='Lozi')
        nyanja = Language.objects.create(slug='nya', name='Nyanja')
        tonga = Language.objects.create(slug='ton', name='Tonga')

        self.assertEqual(Language.objects.count(), 4)

        Dictionary.objects.create(language=lozi, key_phrase='Facility Birth', translation='Sipepo')
        Dictionary.objects.create(language=tonga, key_phrase='Facility Birth', translation='Kuzyalwa')
        Dictionary.objects.create(language=tonga, key_phrase='Home Birth', translation='Kuzyalwa mu nganda')
        Dictionary.objects.create(language=lozi, key_phrase='Home Birth', translation='Sipepo mwa hae')
        Dictionary.objects.create(language=lozi, key_phrase='Birth', translation='Sipepo')
        Dictionary.objects.create(language=tonga, key_phrase='Birth', translation='Kuzyalwa')
        Dictionary.objects.create(language=nyanja, key_phrase='Birth', translation='Kubeleka', alt_translations_one='Mwana')
        Dictionary.objects.create(language=nyanja, key_phrase='her', translation='iwo')
        Dictionary.objects.create(language=nyanja, key_phrase='6 day', translation='tsiku lokwanila 6')
        Dictionary.objects.create(language=nyanja, key_phrase='6 week', translation='sabata lokwanila 6')
        Dictionary.objects.create(language=nyanja, key_phrase='6 month', translation='mwezi wokwanila 6')
        Dictionary.objects.create(language=nyanja, key_phrase='Home Birth', translation='kubelekela kunyumba')
        Dictionary.objects.create(language=nyanja, key_phrase='Facility Birth', translation='kubelekela kukiliniki')
        Dictionary.objects.create(language=bemba, key_phrase='Facility Birth', translation='ukupaapila pa kiliniki')
        Dictionary.objects.create(language=bemba, key_phrase='Home Birth', translation="ukupaapila ku ng'anda")
        Dictionary.objects.create(language=bemba, key_phrase='6 month', translation='mwenshi uwalenga 6')
        Dictionary.objects.create(language=bemba, key_phrase='6 week', translation='mulungu uwalenga 6')
        Dictionary.objects.create(language=bemba, key_phrase='6 day', translation='bushiku bwalenga 6')
        Dictionary.objects.create(language=bemba, key_phrase='her', translation='yabo')
        Dictionary.objects.create(language=bemba, key_phrase='Birth', translation='Ukupaapa', alt_translations_one='Mwana')

        self.assertEqual(Dictionary.objects.count(), 20)


       

class LanguagesTest(LangaugeSetup):

    def runTests(self, lang_code, lang_script):
        self.assertEqual(Dictionary.objects.count(), 20)
        input_phrases = MESSAGES.format(language=lang_code).strip().split('\n')
        responses = lang_script.strip().split('\n')

        self.assertEqual(len(input_phrases), len(responses), "The number of messages in the scripts do not match")

        for i in range(len(input_phrases)):
            script = '''
            097911111 > {input}
            097911111 < {output}
            '''.format(input=input_phrases[i].strip(), output=responses[i].strip()).strip()
            
            self.runScript(script)

    def testBembaTranslation(self):
        "TODO: Add test cases for messages in tasks"
        
        lang_code = 'bem'
        lang_script = '''
            Natoteela Michael Kaseba! Mwakwanisha ukulembesha nga Kafwa wa RemindMi wa zone 2 iya Kafue District Hospital. Mukwayi mukatwebe elyo umuntu akapaapa munchende yenu.
            Twatotela ba Michael Kaseba, mwalembesha ukupaapa kwa ba laura pa 04/03/2010. Tukamyeba inshita yabo ngayafika iyakuya ku chipatala.
            Natoteela ba Michael Kaseba! Mwalembesha ukupaapila ku ng'anda ukwaba laura pa 04/03/2010. Mukebwa inshita yabo ngayafika iyakuya ku chipatala.
            Natoteela ba Michael Kaseba! Mwalembesha ukupaapila pa kiliniki ukwaba laura pa 04/03/2010. Mukebwa inshita yabo ngayafika iyakuya ku chipatala.
            Ba Michael Kaseba, inshita yaba laura ukuya kuchipatala pa bushiku bwalenga 6 pa {next_appointment_date} naifika. Bebukisheni ukuya ku Kafue District Hospital, elyo mutume ati TOLD laura
            Natoteela Michael Kaseba! Panuma ya kushininksha patient 1 aliya ku kiliniki, napapata tumeeni ishiwi lya: CONFIRM patient 1.
            Natoteela Michael Kaseba! Mwashininkisha ukuti patient 2 aliya ku kiliniki
            Njeleleeniko, mulekwata ubwafya ba Michael Kaseba. Ubwafya bwenu bwapeelwa kuli umo uwa mwibumba lya bakafwa kabili balamitumina lamya nomba line
            Ishiwi ilya lubana. Amashiwi yeneyene ni aya: BIRTH, MWANA, TOLD, CONFIRM. Asukeeni ne shiwi ilikankala ilili lyonse nangula HELP pakuti mupokelele imbila imbi.
            Munjeleleko, teti mulembeshe ukupaapa pa nshiku iyishilafika.
            Munjeleleko, nshumfwile inshiku. Lelo tumenu nga ifi - UBUSHIKU UMWENSHI UMWAKA. Ichilangililo: 23 04 2010.
            Njeleleeniko, nshacumfwa iyo imbila. Pakulembesha ukupaapa, tumeni MWANA <DATE> <ISHINA LYABANINA>. Ichilangililo, MWANA 12 3 2012 Loveness Bwalya.
            Njeleleeniko, nshacumfwa iyo imbila. Pakulembesha ukupaapa, tumeni MWANA <DATE> <ISHINA LYABANINA>. Ichilangililo, MWANA 12 3 2012 Loveness Bwalya.
        '''.format(next_appointment_date=(date.today() + timedelta(days=3)).strftime("%d/%m/%Y"))        
        self.runTests(lang_code, lang_script)

    def testNyanjaTranslation(self):
        "TODO: Add test cases for messages in tasks"

        lang_code = 'nya'
        lang_script = '''
            Zikomo Michael Kaseba! Mwakwanitsa kulembetsa ngati wothandiza wa RemindMi wa zone 2 la Kafue District Hospital. Pepani mukatidziwitse kukabadwa mwana mumudzi mwanu.
            Zikomo Michael Kaseba! Mwalembetsa kubeleka kwa laura pa 04/03/2010. Mudzaziwitsidwa pamene nthawi iwo yopita ku kiliniki.
            Zikomo Michael Kaseba! Mwalembetsa kubelekela kunyumba kwaba laura pa 04/03/2010. Mudzaziwitsidwa pamene nthawi iwo yopita ku kiliniki.
            Zikomo Michael Kaseba! Mwalembetsa kubelekela kukiliniki kwaba laura pa 04/03/2010. Mudzaziwitsidwa pamene nthawi iwo yopita ku kiliniki.
            Mooni Michael Kaseba. Nthawi yaba laura yopita ku kiliniki pa tsiku lokwanila 6 pa 22/05/2014 yafika. Chonde akumbukiritseni kupita ku Kafue District Hospital, ndipo yankhulani ndi liwu la TOLD laura.
            Zikomo Michael Kaseba! Pambuyo posimikiza patient 1 anapita ku kiliniki, chonde tumizani: CONFIRM patient 1.
            Zikomo Michael Kaseba! Mwasimikiza kuti patient 2 apita ku kiliniki!
            Pepani, muli ndi mabvuto Michael Kaseba. Bvuto lanu lapatsidwa ku umodziwagulu lothandiza ndipo akuitaneni posachedwa
            Liwu losakwanira. Mawu yokwanira ndi: BIRTH, MWANA, TOLD, CONFIRM. Yankhulani ndi liwu lokwanira liri lonse kapena HELP kuti mulandire uthenga wina.
            Pepani simungathe kulembetsa kubeleka ndi tsiku kuposa pa la lelo
            sindinamvere tsiku ilo. Chonde lembani ilo tsiku monga: DAY, MONTH YEAR mwachisanzo: 23 04 2010.
            Pepani sindinamvere icho. Poongeza kubeleka, tumizani MWANA <DATE> <NAME>. Mwachisanzo, MWANA 12 3 2012 Loveness Bwalya.
            Pepani sindinamvere icho. Poongeza kubeleka, tumizani MWANA <DATE> <NAME>. Mwachisanzo, MWANA 12 3 2012 Loveness Bwalya.
        '''.format(next_appointment_date=(date.today() + timedelta(days=3)).strftime("%d/%m/%Y"))
        self.runTests(lang_code, lang_script)
