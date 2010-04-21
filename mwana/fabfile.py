from __future__ import with_statement

import os
import sys
import tempfile

from fabric.api import run, local, settings, env, put, hide, show
from fabric.contrib import files, console, project
from fabric import utils


# use this instead of os.path.join since remote OS might differ from local
PATH_SEP = '/'
RSYNC_EXCLUDE = (
    '*~',
    '.git',
    '*.pyc',
#    '*.example',
    'fabfile.py',
    'localsettings.py',
    'media/photos/',
)
WRITABLE_MEDIA_DIRS = (
    'photos',
)
env.project = 'mwana'
# remove -l from env.shell, "mesg n" in ~/.profile was causing issues
# see Why do I sometimes see ``err: stdin: is not a tty``?
# http://github.com/bitprophet/fabric/blob/master/FAQ
env.shell = '/bin/bash -c'


def setup_path():
    env.path = PATH_SEP.join((env.root, env.environment))


def dev():
    env.environment = 'dev'
    env.hosts = ['mwana']
    env.user = 'deployer'
    env.root = '/home/deployer'
    env.dbname = 'mwana_dev'
    setup_path()


def staging():
    env.environment = 'staging'
    env.hosts = ['mwana']
    env.user = 'deployer'
    env.root = '/home/deployer'
    env.dbname = 'mwana_staging'
    setup_path()


def production():
    if not console.confirm('Are you sure you want to set the environment to '
                           'production?', default=False):
        utils.abort('Production deployment aborted.')
    env.environment = 'production'
    env.hosts = ['66.36.213.161']
    env.user = 'mwana'
    env.root = '/home/mwana'
    env.dbname = 'mwana_production'
    setup_path()


def deploy():
    # don't die if tests fail
    # with settings(warn_only=True):
    #     run_tests()
    # defaults rsync options:
    # -pthrvz
    # -p preserve permissions
    # -t preserve times
    # -h output numbers in a human-readable format
    # -r recurse into directories
    # -v increase verbosity
    # -z compress file data during the transfer
    extra_opts = '--omit-dir-times'
    project.rsync_project(
        env.path,
        exclude=RSYNC_EXCLUDE,
        delete=True,
        extra_opts=extra_opts,
    )
    touch()


def run_tests():
    local('./manage.py test', capture=False)


def touch():
    run('touch %s' % PATH_SEP.join((env.path, 'mwana', 'apache', 'project.wsgi')))

