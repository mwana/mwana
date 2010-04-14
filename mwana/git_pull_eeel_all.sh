#!/bin/sh

# update mwana
git pull eeel master

# update rapidsms-core-dev
cd submodules/rapidsms
git pull eeel master

# update rapidsms-contrib-apps-dev
cd lib/rapidsms/contrib
git pull eeel master
