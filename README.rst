mwana
=====

This is the Mwana MNCH RapidSMS project for deployment in Zambia and Malawi. It
includes Results160, a tool for delivering DBS test results to health clinic
workers, and RemindMi, a birth registration and appointment reminder system
for community based agents (such as CHWs and HSAs).

Development Workflow
====================

We are using git-flow to help manage our development process.

Learn how to use git-flow at:
  http://jeffkreeftmeijer.com/2010/why-arent-you-using-git-flow/

You can download and install git-flow from:
  https://github.com/nvie/gitflow

Learn more about the methodology behind it at:
  http://nvie.com/posts/a-successful-git-branching-model/

Developer Setup
===============

**Prerequisites:**

* Install pip and virtualenv, and make sure virtualenv is up to date, e.g.::

    easy_install pip
    pip install -U virtualenv
    pip install -U virtualenvwrapper

* Install git-flow (see above).

**To setup a local development environment, follow these steps:**

#. Clone the code from git, checkout the ``develop`` branch, and initialize
   git-flow::

    git clone git@github.com:mwana/mwana.git
    cd mwana/mwana
    git checkout develop
    git flow init # just accept all the default answers
  
#. Create a Python virtual environment for this project::

    mkvirtualenv --distribute mwana-dev
    workon mwana-dev

#. Install the project dependencies into the virtual environment::

    ./bootstrap.py

#. Create local settings file and initialize a development database::

    cp localsettings.py.example localsettings.py
    gedit localsettings.py # replace <country> with zambia or malawi in the first line
    createdb mwana_devel
    ./manage.py syncdb

#. In one terminal, start RapidSMS router::

    mkdir logs
    ./manage.py runrouter

#. In another terminal, start the Django development server::

    ./manage.py runserver

#. Open http://localhost:8000 in your web browser and you should see an
   **Installation Successful!** screen.

