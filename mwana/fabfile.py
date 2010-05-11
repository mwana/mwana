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
# if you get errors checking out "master", you probably need to run
# "git branch master" in the offending repository on the server
COMMITS = (
    ('mwana', 'master'),
    ('rapidsms-core-dev', 'master'),
    ('rapidsms-contrib-apps-dev', 'master'),
#    ('pygsm', 'master'),
    ('django-tables', '2433617df7bf60025a32d56b36e081f7ef1aa5e6'),
    ('django-app-settings', '54935e8bcd155206ff4f296d8fa067006ba7bbda'),
)
DEST_DIRS = {
    'mwana': '',
    'rapidsms-core-dev': 'mwana/submodules/rapidsms',
    'rapidsms-contrib-apps-dev': 'mwana/submodules/rapidsms/lib/rapidsms/contrib',
#    'pygsm': '',
    'django-tables': 'mwana/submodules/rapidsms/submodules/django-tables',
    'django-app-settings': 'mwana/submodules/rapidsms/submodules/django-app-settings',
}
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
    env.repos = {
        'mwana': '/home/projects/mwana',
        'rapidsms-core-dev': '/home/projects/rapidsms-core-dev',
        'rapidsms-contrib-apps-dev': '/home/projects/rapidsms-contrib-apps-dev',
#        'pygsm': '/home/projects/pygsm',
        'django-tables': '/home/projects/django-tables',
        'django-app-settings': '/home/projects/django-app-settings',
    }
    setup_path()


def production():
    if not console.confirm('Are you sure you want to set the environment to '
                           'production?', default=False):
        utils.abort('Production deployment aborted.')
    env.environment = 'production'
    env.hosts = ['41.72.110.86:80']
    env.user = 'mwana'
    env.root = '/home/mwana'
    env.dbname = 'mwana_production'
    env.repos = {
        'mwana': 'git://github.com/mwana/mwana.git',
        'rapidsms-core-dev': 'git://github.com/mwana/rapidsms-core-dev.git',
        'rapidsms-contrib-apps-dev':
            'git://github.com/mwana/rapidsms-contrib-apps-dev.git',
#       'pygsm': 'git://github.com/mwana/pygsm',
        'django-tables': 'git://github.com/adammck/django-tables.git',
        'django-app-settings': 'git://github.com/adammck/django-app-settings.git',
    }
    setup_path()


def deploy_from_local():
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
    extra_opts = '--omit-dir-times -e "ssh -p 80"'
    project.rsync_project(
        env.path,
        exclude=RSYNC_EXCLUDE,
        delete=True,
        extra_opts=extra_opts,
    )
    touch()
    restart_route()


def iter_commits():
    for name, commit in COMMITS:
        repo = env.repos.get(name, '')
        # don't use os.path on the off chance that we're deploying
        # from windows to linux
        dest = env.path + '/' + DEST_DIRS.get(name, '')
        yield name, commit, repo, dest


def clone_all():
    for name, commit, repo, dest in iter_commits():
        if repo:
            run('git clone %s %s' % (repo, dest))


def pull_and_checkout_all():
    for name, commit, repo, dest in iter_commits():
        if repo:
            run('cd %s && git pull origin master && git checkout %s' %
                (dest, commit))


def deploy():
    pull_and_checkout_all()
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
    run("sudo sed -i 's/PROJECT_DIR=/PROJECT_DIR=%s/' /etc/init.d/mwana-route"
        % env.path.replace('/', '\/'))
    run("sudo sed -i 's/USER=/USER=%s/' /etc/init.d/mwana-route"
        % env.user)


def restart_route():
    """
    Restarts the RapidSMS route process on the remote server.  Requires sudo
    permissions on /etc/init.d/mwana-route, e.g.:
    
    deployer ALL=NOPASSWD: ALL
    """
    # using run instead of sudo because sudo prompts for a password
    run('sudo /etc/init.d/mwana-route restart')
    # print out the top of the log file in case there are errors
    import time
    time.sleep(2)
    run('head -n 15 %s/route.log' % env.path)


def syncdb():
    """
    Runs ./manage.py syncdb on the remote server.
    """
    run('%s/mwana/manage.py syncdb' % env.path)


def bootstrap():
    """
    Bootstraps the remote server for the first time.  This is just a shortcut
    for the other more granular methods.
    """
    install_init_script()
    clone_all()
    put('localsettings.py.example', '%s/mwana/localsettings.py' % env.path)
    pull_and_checkout_all()
    print '\nNow add your database settings to localsettings.py and run syncdb'
