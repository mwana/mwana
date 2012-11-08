from django.db import models


class ContactLocation(models.Model):
    unique_id = models.CharField(max_length=255, blank=True, null=True, unique=True,
                                 help_text="An optional Unique Identifier for this contact")

    class Meta:
        abstract = True

    def get_current_district(self):
        """
        Returns the district associated with the user's current location
        """
        location = self.location
        loc_type = location.type.singular.lower()
        while loc_type != 'district':
            location = location.parent
            loc_type = location.type.singular.lower()
        return location

    def get_current_facility(self):
        """
        Returns the facility associated with the user's current location
        """
        location = self.location
        while location.parent.type.singular.lower() != 'district':
            location = location.parent
        return location
