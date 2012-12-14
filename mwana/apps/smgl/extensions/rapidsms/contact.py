from datetime import datetime

from django.db import models


class ContactLocation(models.Model):
    unique_id = models.CharField(max_length=255, blank=True, null=True, unique=True,
                                 help_text="An optional Unique Identifier for this contact")

    created_date = models.DateField(auto_now_add=True)
    return_date = models.DateField(null=True, blank=True,
                                  help_text="The Date a user will return to being active")
    is_super_user = models.BooleanField(default=False,
                     help_text="Whether this user should receive emergency related messages.")

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

    @property
    def latest_sms_date(self):
        model = models.get_model('messagelog', 'Message')
        latest = model.objects.filter(
            contact=self.id,
            direction='I',
        ).aggregate(date=models.Max('date'))
        if latest['date']:
            return latest['date']
        else:
            return None

    @property
    def active_status(self):
        status = 'inactive'
        if self.latest_sms_date:
            now = datetime.now()
            days = (now - self.latest_sms_date).days
            if days <= 10:
                status = 'active'
            elif days <= 14:
                status = 'short-term-inactive'
        return status
