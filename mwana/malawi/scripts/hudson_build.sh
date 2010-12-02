#!/bin/bash -ex
ENV=env
rm -rf $ENV
virtualenv --clear --distribute $ENV
source $ENV/bin/activate
cd mwana/requirements
pip install -q -r hudson.txt
cd ..
./bootstrap.py
# make sure it works with the malawi country-wide configuration
./manage.py test --noinput --settings=mwana.malawi.settings_hudson --mwana-apps
