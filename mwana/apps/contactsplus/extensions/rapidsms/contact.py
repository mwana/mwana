# vim: ai ts=4 sts=4 et sw=4

from django.db import models


class ContactType(models.Model):

    types = models.ManyToManyField('contactsplus.ContactType',
                                   related_name='contacts', blank=True)
    is_active = models.BooleanField(default=True)

    def __init__(self, *args, **kwargs):
        super(ContactType, self).__init__(*args, **kwargs)
        self._clinic = None
        self._district = None

    @property
    def clinic(self):
        from mwana import const

        if not self._clinic and self.location:
            if self.location.type.slug in const.ZONE_SLUGS:
                self._clinic = self.location.parent
            elif self.location.type.slug in const.CLINIC_SLUGS:
                self._clinic = self.location
        return self._clinic

    @property
    def district(self):
        from mwana import const

        if not self._district and self.location:
            clinic = self.clinic
            if clinic and clinic.parent:
                self._district = clinic.parent
            elif self.location.type.slug in const.DISTRICT_SLUGS:
                self._district = self.location
        return self._district

    class Meta:
        abstract = True


class ContactParent(models.Model):
    """To relate mother and child pair patients."""
    parent = models.ForeignKey('self', null=True, blank=True)

    class Meta:
        abstract = True
