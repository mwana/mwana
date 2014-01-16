# vim: ai ts=4 sts=4 et sw=4
from mwana.apps.translator.models import Dictionary
import logging


logger = logging.getLogger(__name__)


class Translator:
    """
    Complements django gettext based translator. Specially used to translate dynamic phrases in formatted strings
    """

    dictionary = {}
    dictionary_one = {}
    dictionary_two = {}


    def __init__(self):
        try:
            for obj in Dictionary.objects.all():
                self.dictionary["%s:%s" % (obj.language.slug.lower(), obj.key_phrase.lower())] = obj.translation

            for obj in Dictionary.objects.all().exclude(alt_translations_one=None):
                self.dictionary_one["%s:%s" % (obj.language.slug.lower(), obj.key_phrase.lower())] = obj.alt_translations_one
        except Exception, e:
            logger.warning("%s" % e)

    def translate(self, language_code, key_phrase, alternate=0):
        if not (language_code and key_phrase):
            return key_phrase
        
        if alternate == 0:
            try:
                return self.dictionary["%s:%s" % (language_code.strip().lower(), key_phrase.strip().lower())]
            except Exception, e:
                logger.error("could not do custom translation for %s. It is likely missing in the disctionary." % e.message)
                return key_phrase
        elif alternate == 1:
            try:
                return self.dictionary_one["%s:%s" % (language_code.strip().lower(), key_phrase.strip().lower())]
            except Exception, e:
                logger.error("could not do alternate custom translation for %s. It is likely missing in the disctionary." % e.message)
                return key_phrase
            
    