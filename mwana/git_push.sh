#!/bin/sh

# update mwana
git push $1 master

# update rapidsms-core-dev
cd submodules/rapidsms
git push $1 master

# update rapidsms-contrib-apps-dev
cd lib/rapidsms/contrib
git push $1 master
