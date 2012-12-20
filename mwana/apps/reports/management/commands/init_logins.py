# vim: ai ts=4 sts=4 et sw=4
""" Initialises the table that stores information on whether someone has logged
in before
"""
from django.contrib.auth.models import User
from mwana.apps.reports.models import Login
from django.core.management.base import LabelCommand


class Command(LabelCommand):   

    def handle(self, * args, ** options):
        for user in User.objects.all():
            login = Login.objects.get_or_create(user=user)[0]
            login.ever_logged_in = user.last_login != user.date_joined
            login.save()