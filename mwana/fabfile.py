from __future__ import with_statement

import os
import sys
import tempfile

from fabric.api import run, local, settings, env, put, hide, show, sudo
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
    env.hosts = ['41.72.110.86']
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
    restart_route()


def run_tests():
    local('./manage.py test', capture=False)


def touch():
    """
    Forces a reload of the WSGI Django application in Apache by modifying
    the last-modified time on the wsgi file.
    """
    run('touch %s' % PATH_SEP.join((env.path, 'mwana', 'apache', 'project.wsgi')))


def install_init_script():
    """
    Installs the init script for the RapidSMS route script in the /etc/init.d
    directory for the first time and adds it to the default run levels so that
    it's started and stopped appropriately on boot/shutdown.  Requires sudo
    permissions on /etc/init.d/mwana-route, e.g.:
    
    deployer ALL=NOPASSWD: ALL    
    """
    run('sudo touch /etc/init.d/mwana-route')
    run('sudo chown %s /etc/init.d/mwana-route' % env.user)
    run('sudo update-rc.d mwana-route defaults')
    update_init_script()


def update_init_script():
    """
    Updates the init script for the RapidSMS route script in the /etc/init.d
    directory.  Requires that the file (/etc/init.d/mwana-route) already exists
    with write permissions for the deploying user.
    
    Run install_init_script before calling this method.
    """
    put('scripts/mwana-route-init-script.sh', '/etc/init.d/mwana-route', 0755)


def restart_route():
    """
    Restarts the RapidSMS route process on the remote server.  Requires sudo
    permissions on /etc/init.d/mwana-route, e.g.:
    
    deployer ALL=NOPASSWD: ALL
    """
    # using run instead of sudo because sudo prompts for a password
    run('sudo /etc/init.d/mwana-route restart')
