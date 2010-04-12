from django.db import models


class Message(models.Model):
    """
    An actual text message to be delivered to a user.  This is just a place
    holder model that all the translations of this message link to.
    """
    name = models.CharField(max_length=100)
    text = models.CharField(max_length=160)

    def __unicode__(self):
        return self.name
