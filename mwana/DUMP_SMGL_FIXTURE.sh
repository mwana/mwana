#!/bin/sh
python manage.py dumpdata --indent 2 contactsplus.ContactType locations.LocationType locations.Location smgl.XFormKeywordHandler smsforms.DecisionTrigger formplayer.XForm