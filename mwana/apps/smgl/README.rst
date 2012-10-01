Code Description Doc
====================

Getting Setup:

External apps: CouchDB

install dependencies
$ cd requirements
$ pip install -r bu_reqs.txt
$ pip install -r libs.txt


High Level Tech Overview
------------------------

This application started with the mwana repo and was repurposed for this project. There is a ton of cruft floating around that is not doing anything because of that. Almost all of the functionality lives in this app's folder.
 
The core functionality currently is a bunch of forms that are made in xforms, as well as an xforms editor and an xform survey player which supports two different modes - one question at a time and the entire form at once.

This is handled by the rapidsms-smsforms app. That app uses a jython process and java lib (touchforms)to actually play the forms. Both projects have decent docs:
 - https://github.com/dimagi/rapidsms-smsforms
 - https://github.com/dimagi/touchforms

Once the xforms are received, we dump them to Couch DB using the same libs used in CommCare HQ (couchforms), plus a little glue app called rapidsms-smscouchforms. Once in couch the forms can be exported in various formats using couchexport
 - https://github.com/dimagi/rapidsms-smscouchforms
 - https://github.com/dimagi/couchforms
 - https://github.com/dimagi/couchexport

The project forms live in mwana/xforms, and are automatically loaded on syncdb.

The SMGL app has an infrastructure that hooks into a signal to receive new forms, and then routes the message to a post-processing function to create project-specific data models. Most of these live in mwana.apps.smgl.keyword_handlers.
 - The mapping for those is stored in the database, and in the initial_data.json fixture (see below).


smgl/fixtures/initial_data.json
-------------------------------

*Note* you should look at the fixtures file as it will be loaded and overwrite anything else present everytime you syncdb.  Make sure this file stays up to date!
The fixture file is essential for unit testing (or you'd have to create all the structures by hand and ensure that they're in sync with what's really happening on production).
The fixture file contains:

* Contact Types essential to the project
* Location Types 
* Locations: all locations to be used in the pilot phase
* DecisionTriggers: the actual keyword used to trigger a specific workflow (all ones that are used by this pilot project)
* XFormKeywordHandlers these all link the DecisionTriggers to post_processing handlers.  Configured for this pilot project.

smgl/locale/*
-------------
Ready made django translation datafiles used by Rosetta.  May need to be 
updated, see django's `compilemessages` and `makemessages` admin commands.

To regenerate message files run:

cd mwana/apps/smgl
django-admin.py makemessages -l en
django-admin.py makemessages -l to
django-admin.py compilemessages

smgl/admin.py
--------------

Sets up the admin views to make it more user friendly.  The Zambia SMGL staff 
will have (permission limited) access to the admin view.  They are comfortable 
with using the admin interface per their experience with the mwana project.


smgl/ambulance_workflow.py
--------------------------

All xform_saved_with_session Signal handlers associated with the ambulance workflow belong here.

Various utility function are all marked as such by prepending a '_' to the function.

ALL HARDCODED STRINGS ARE LOCATED IN `mwana/apps/smgl/app.py` in order to keep strings centralized in one place for easier editing.

smgl/rapidsms_migrations/*
--------------------------
THESE ARE IMPORTANT.  These migrations allow us to modify rapidsms core models (using the extension framework) without fiddlying with actual core code.

smgl/join_handler.py
--------------------
Handles the pre-registration and ultimate joining of new SMS users to the system.
(see models.py: PreRegistration)

smgl/app.py
-----------
ALL OTHER WORFLOWS.  This needs to be broken down in similar way to ambulance_workflow and join_handler to keep the file clean and easy to understand.

* Contains a ton of _utility functions used by this and other workflows.
* Contains the pregnant_registration handler
* Contains the follow_up handlers
* Placeholders for referral, birth and death registration.
* Contains core code for how xform_saved signal gets handled and delegated out to the handler functions (see `handle_submission()` )

smgl/models.py
--------------
Fairly straightforwad.  Contains 
* ORM models for mother pregnancy
* various stages of ambulance workflow
* XFormKeywordHanlder model
* FacilityVisit