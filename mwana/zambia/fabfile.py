from __future__ import with_statement

import os
import sys
import tempfile

from fabric.api import run, local, settings, env, put, hide, show, sudo, cd
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
env.local_dir = os.path.dirname(os.path.dirname(__file__))

# if you get errors checking out "master", you probably need to run
# "git branch master" in the offending repository on the server
COMMITS = (
    ('mwana', 'new-core'),
)
DEST_DIRS = {
    'mwana': env.project,
}

def setup_path():
    env.code_root = os.path.join(env.root, env.project)
    env.virtualenv_root = os.path.join(env.root, 'env')


def dev():
    env.environment = 'dev'
    env.hosts = ['mwana']
    env.user = 'deployer'
    env.root = '/home/deployer'
    env.dbname = 'mwana_dev'
    setup_path()


def staging():
    env.environment = 'staging-newcore'
    env.hosts = ['mwana']
    env.user = 'deployer'
    env.home = '/home/deployer'
    env.root = os.path.join(env.home, env.environment)
    env.dbname = 'mwana_staging_newcore'
    env.repos = {
#        'mwana': '/home/projects/mwana',
        'mwana': 'https://adewinter@github.com/mwana/mwana.git',
    }
    setup_path()


def production():
    if not console.confirm('Are you sure you want to set the environment to '
                           'production?', default=False):
        utils.abort('Production deployment aborted.')
    env.environment = 'production'
    env.hosts = ['41.72.110.86:80']
    env.user = 'mwana'
    env.home = '/home/mwana'
    env.root = os.path.join(env.home, env.environment)
    env.dbname = 'mwana_production'
    env.repos = {
        'mwana': 'git://github.com/mwana/mwana.git',
    }
    setup_path()


def create_virtualenv():
    args = '--clear --distribute'
    run('rm -rf %s' % env.virtualenv_root)
    run('virtualenv %s %s' % (args, env.virtualenv_root))


def update_requirements():
    with cd(PATH_SEP.join([env.code_root, env.project, 'requirements'])):
        run('pwd')
        for file_name in ['libs.txt']:
            cmd = ['pip install']
            cmd += ['-q -E %(virtualenv_root)s' % env]
            cmd += ['--no-deps']
            cmd += ['--requirement %s' % file_name]
            run(' '.join(cmd))


def deploy_from_local():
    """
    Deploys to hosts using local files and rsync (instead of checking out from a remote repo). Touches wsgi script to force apache reload.
    """
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
    extra_optss = '--omit-dir-times -e "ssh"' # -p 80"'
    project.rsync_project(
        env.code_root,
        local_dir=env.local_dir,
        exclude=RSYNC_EXCLUDE,
        delete=True,
        extra_opts=extra_optss,
    )
    touch()
    restart_route()


def iter_commits():
    for name, branch in COMMITS:
        repo = env.repos.get(name, '')
        # don't use os.path on the off chance that we're deploying
        # from windows to linux
        dest = PATH_SEP.join([env.root, DEST_DIRS.get(name, '')])
        yield name, branch, repo, dest


def clone_all():
    for name, branch, repo, dest in iter_commits():
        if repo:
            run('git clone %s %s' % (repo, dest))


def pull_and_checkout_all():
    for name, branch, repo, dest in iter_commits():
        if repo:
            run('cd %s && git pull origin master && git checkout %s' %
                (dest, branch))


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
    run('touch %s' % PATH_SEP.join((env.code_root,'mwana', 'zambia', 'apache',
                                    'project.wsgi')))


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
    init_script = os.path.join(env.local_dir, 'scripts',
                               'mwana-route-init-script.sh')
    put(init_script, '/etc/init.d/mwana-route', 0755)
    run("sudo sed -i 's/PROJECT_DIR=/PROJECT_DIR=%s/' /etc/init.d/mwana-route"
        % env.root.replace('/', '\/'))
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
    run('head -n 15 %s/route.log' % env.root)


def syncdb():
    """
    Runs ./manage.py syncdb on the remote server.
    """
    run('%s/mwana/manage.py syncdb' % env.root)


def bootstrap():
    """
    Bootstraps the remote server for the first time.  This is just a shortcut
    for the other more granular methods.
    """
    create_virtualenv()
    install_init_script()
    if not files.exists(env.code_root):
        clone_all()
    put(os.path.join(env.local_dir, 'localsettings.py.example'),
        PATH_SEP.join([env.root, 'mwana', 'localsettings.py']))
    pull_and_checkout_all()
    update_requirements()
    print '\nNow add your database settings to localsettings.py and run syncdb'
