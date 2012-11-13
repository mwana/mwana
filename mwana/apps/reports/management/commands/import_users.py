# vim: ai ts=4 sts=4 et sw=4
"""
Creates web users from a csv file. The fields in the csv file must be in the
order: FirstName, LastName, Email, Type, District. Passwords created are 'temporal'
"""

from mwana.apps.reports.webreports.models import GroupUserMapping
from mwana.apps.reports.webreports.models import ReportingGroup
import os
import os.path

from django.core.management.base import CommandError
from django.core.management.base import LabelCommand

class Command(LabelCommand):
    help = "Loads users from the specified csv file."
    args = "<file_path> <password_suffix>"
    label = 'valid file path'

    def handle(self, * args, ** options):
        if len(args) < 1:
            raise CommandError('Please specify %s.' % self.label)
        file_path = (args[0])


        load_users(file_path)

    def __del__(self):
        pass

def load_users(file_path):
    from django.contrib.auth.models import User
    from datetime import date

    if not os.path.exists(file_path):
        raise CommandError("Invalid file path: %s." % file_path)


    csv_file = open(file_path, 'r')


    for line in csv_file:
        #leave out header
        if "email" in line.lower():
            continue

        first_name, last_name, email, user_type, district_name = line.split(",")[:5]

        first_name = first_name.strip()
        last_name = last_name.strip()
        email = email.strip()
        district_name = district_name.strip()
        user_type = user_type.strip()

        if "@" not in email:
            print "%s is not a valid email" % email
            continue

        username = first_name[0].lower() + last_name.lower()

        password = "%s%s" % (username, date.today().day)

        if User.objects.filter(username=username):
            print "%s exists. Skipping %s" % (username, line)
            continue

        user = User(username=username, first_name=first_name,
                    last_name=last_name, email=email, is_staff=True)
        user.set_password(password)
        user.save()

        print "Created login: %s , password: %s, for %s %s " % (username, password, first_name, last_name)

        group, created = ReportingGroup.objects.get_or_create(name=("%s %s" % (user_type, district_name)).strip())
        if created:
            gum, c = GroupUserMapping.objects.get_or_create(user=user, group=group)
            print "Created GroupUserMapping: %s %s"% (gum, c)

