# vim: ai ts=4 sts=4 et sw=4

from django.db import models



class Language(models.Model):
    slug = models.CharField(max_length=6, null=False, blank=False, unique=True)
    name = models.CharField(max_length=50, null=False, blank=False)

    def __unicode__(self):
        return self.name


class Dictionary(models.Model):
    """
    Dictionary
    """

    language = models.ForeignKey(Language, null=False, blank=False)
    key_phrase = models.CharField(max_length=255, null=False, blank=False, verbose_name="English term")
    description = models.CharField(max_length=255, null=True, blank=True)
    translation = models.CharField(max_length=255, null=False, blank=False)
    alt_translations_one = models.CharField(max_length=255, null=True, blank=True)
    alt_translations_two = models.CharField(max_length=255, null=True, blank=True)

    

    def __unicode__(self):
        return "%s, %s: %s" % (self.language, self.key_phrase, self.translation[:20])

    class Meta:
        unique_together = (('language', 'key_phrase',),)
        verbose_name_plural = "Dictionary Entries"

