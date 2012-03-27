# vim: ai ts=4 sts=4 et sw=4

from django.db import models

class NutritionLocation(models.Model):
    population = models.IntegerField('Catchment Population')
    census = models.IntegerField('Census Data', default=10000)

    class Meta:
        abstract = True

