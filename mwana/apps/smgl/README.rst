====================
Code Description Doc
====================

Developer Setup
===============

**Prerequisites:**

* A Linux-based development environment including Python 2.6.  Ubuntu 10.04 or
  later is recommended.  At present, Windows-based environments are not
  actively supported.

* PostgreSQL and the appropriate Python bindings (``psycopg2``).  In
  Debian-based distributions, you can install these using ``apt-get``, e.g.::

    sudo apt-get install postgresql libpq-dev

* The following additional build dependencies::

    sudo apt-get install libxslt1-dev libxml2-dev

* CouchDB is required for logging and audit tracking purposes. See
  http://wiki.apache.org/couchdb/Installing_on_Ubuntu for more information about CouchDB::

    sudo apt-get install couchdb

* Jython is required for the Touchforms player::

    wget http://sourceforge.net/projects/jython/files/jython/2.5.2/jython_installer-2.5.2.jar
    sudo java -jar jython_installer-2.5.2.jar
    # Default answers. Target directory /usr/local/lib/jython
    sudo ln -s /usr/local/lib/jython/bin/jython /usr/local/bin/

* Install pip and virtualenv, and make sure virtualenv is up to date, e.g.::

    easy_install pip
    pip install -U virtualenv
    pip install -U virtualenvwrapper


**To setup a local development environment, follow these steps:**

#. Clone the code from Github:

    git clone git@github.com:mwana/mwana.git

#. Checkout the **zhcard_dev** branch::

    git checkout zhcard_dev

#. Create a Python virtual environment for this project::

    mkvirtualenv --distribute mwana
    workon mwana

#. Install the project dependencies into the virtual environment::

    cd requirements
    pip install -r libs.txt
    pip install -r bu_reqs.txt

#. Create local settings file and initialize a development database::

    cp localsettings.py.example localsettings.py
    createdb mwana
    ./manage.py syncdb
    ./manage.py migrate


#. Update the submodules::

    git submodule init
    git submodule update

#. In a terminal, start the Django development server::

    ./manage.py runserver

#. In another terminal, start the XForms player::

    cd submodules/touchforms/touchforms/backend/
    jython xformserver.py 4444

#. Open http://localhost:8000 in your web browser and you should see an
   **Installation Successful!** screen.


General Information
===================

The SMGL app (mwana/apps/smgl) contains migrations, *fixtures* and rapidsms-extensions.

smgl/fixtures/initial_data.json
-------------------------------

.. note:: You should look at the fixtures file as it will be loaded and overwrite anything else present everytime you syncdb.  Make sure this file stays up to date!

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

To regenerate message files run::

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
Fairly straightforwad.  Contains:

* ORM models for mother pregnancy
* various stages of ambulance workflow
* XFormKeywordHanlder model
* FacilityVisit
