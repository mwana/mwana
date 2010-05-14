#!/bin/sh

# update mwana
git pull $1 master

# update rapidsms-core-dev
cd submodules/rapidsms
git pull $1 master

# update rapidsms-contrib-apps-dev
cd lib/rapidsms/contrib
git pull $1 master
