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
    def active_status(self, start_date=None, end_date=None):
        #If this is a cba, inactive is 60 days
        is_cba = ['cba'] == list(self.types.all().values_list('slug', flat=True))
        #If we are passed in the start_date and end_date we consider the period
        if start_date and end_date:
            model = models.get_model('messagelog', 'Message')
            messages = model.objects.filter(
                contact=self.id,
                direction='I',
                date__gte=start_date,
                date__lte=end_date
                )
            if messages:
                status = "inactive"
            else:
                status = "active"
        else:
            status = 'inactive'
            inactivity_threshold = 14
            if is_cba:
                inactivity_threshold = 60
            if self.latest_sms_date:
                now = datetime.now()
                days = (now - self.latest_sms_date).days
                if days <= inactivity_threshold:
                    status = 'active'
        return status
