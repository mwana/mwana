Code Description Doc
====================

General.  
The SMGL app (mwana/apps/smgl) contains migrations, *fixtures* and rapidsms-extensions.

smgl/fixtures/initial_data.json
-------------------------------

*Note* you should look at the fixtures file as it will be loaded and overwrite anything else present everytime you syncdb.  Make sure this file stays up to date!
The fixture file contains:

* Contact Types essential to the project
* Location Types 
* Locations: all locations to be used in the pilot phase
* DecisionTriggers: the actual keyword used to trigger a specific workflow (all ones that are used by this pilot project)
* XFormKeywordHandlers these all link the DecisionTriggers to post_processing handlers.  Configured for this pilot project.

smgl/locale/*
-------------
Ready made django translation datafiles used by Rosetta.  May need to be updated,
see django's `compilemessages` and `makemessages` admin commands.

smgl/admin.py
--------------

Sets up the admin views to make it more user friendly.  The Zambia SMGL staff will have (permission limited) access to the admin view.  They are comfortable with using the admin interface per their experience with the mwana project.


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
