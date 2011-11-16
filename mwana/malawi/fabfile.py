# vim: ai ts=4 sts=4 et sw=4
from __future__ import with_statement

import os
import sys
import tempfile
from os.path import dirname, abspath

from fabric.api import *
from fabric.contrib import files, console, project
from fabric import utils

sys.path.insert(0, dirname(dirname(dirname(abspath(__file__)))))

from mwana import localsettings

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
env.repos = {
    'mwana': {'branch': 'develop',
              'url': 'git://github.com/mwana/mwana.git'},
}

# destination for the route process init script
env.init_script = '/etc/init.d/mwana-route'

def setup_path():
    env.root = os.path.join(env.home, env.environment)
    env.code_root = os.path.join(env.root, 'code_root')
    env.virtualenv_root = os.path.join(env.root, 'python_env')


def staging():
    env.environment = 'staging-environment'
    env.hosts = ['10.3.1.10']
    env.user = 'mwana'
    env.home = '/home/mwana'
    env.repos['mwana']['branch'] = 'release/Malawi_1.2'
    setup_path()


def production():
    if not console.confirm('Are you sure you want to set the environment to '
                           'production?', default=False):
        utils.abort('Production deployment aborted.')
    env.environment = 'production-environment'
    env.hosts = ['10.3.1.20']
    env.user = 'mwana'
    env.home = '/home/mwana'
    env.repos['mwana']['branch'] = 'release/Malawi_1.2'
    setup_path()


def create_virtualenv():
    args = '--clear --distribute'
    run('rm -rf %s' % env.virtualenv_root)
    run('virtualenv %s %s' % (args, env.virtualenv_root))


def update_requirements():
    with cd(PATH_SEP.join([env.code_root, env.project, 'requirements'])):
        for file_name in ['libs.txt', 'pygsm.txt']:
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
    extra_opts = '--omit-dir-times -e "ssh"' # -p 80"'
    project.rsync_project(
        env.code_root,
        local_dir=env.local_dir,
        exclude=RSYNC_EXCLUDE,
        delete=True,
        extra_opts=extra_opts,
    )
    touch()
    restart_route()


def iter_commits():
    dest_dirs = {
        'mwana': env.code_root,
    }
    for name, config in env.repos.iteritems():
        yield name, config['branch'], config['url'], dest_dirs.get(name, '')


def clone_all():
    for name, branch, repo, dest in iter_commits():
        if repo:
            run('git clone %s %s' % (repo, dest))


def pull_and_checkout_all():
    for name, branch, repo, dest in iter_commits():
        if repo:
            with cd(dest):
                run('git pull')
                run('git checkout %s' % branch)


def deploy():
    pull_and_checkout_all()
    update_requirements()
    touch()
    restart_route()


def run_tests():
    local('./manage.py test', capture=False)


def touch():
    """
    Forces a reload of the WSGI Django application in Apache by modifying
    the last-modified time on the wsgi file.
    """
    run('touch %s' % PATH_SEP.join((env.code_root, 'mwana', 'malawi', 'apache',
                                    'project.wsgi')))


def install_init_script():
    """
    Installs the init script for the RapidSMS route script in the /etc/init.d
    directory for the first time and adds it to the default run levels so that
    it's started and stopped appropriately on boot/shutdown.  Requires sudo
    permissions on the init script, e.g.:
    
    deployer ALL=NOPASSWD: ALL    
    """
    run('sudo touch %s' % env.init_script)
    run('sudo chown %s %s' % (env.user, env.init_script))
    run('sudo update-rc.d %s defaults' % os.path.basename(env.init_script))
    update_init_script()


def _replace_init_script_var(key, value):
    run("sudo sed -i 's/%s=/%s=%s/' %s" % (key, key, value,
                                           env.init_script))


def update_init_script():
    """
    Updates the init script for the RapidSMS route script in the /etc/init.d
    directory.  Requires that the file (/etc/init.d/mwana-route) already exists
    with write permissions for the deploying user.
    
    Run install_init_script before calling this method.
    """
    init_script = os.path.join(env.local_dir, 'scripts',
                               'mwana-route-init-script.sh')
    put(init_script, env.init_script, 0755)
    _replace_init_script_var('PROJECT_DIR', env.root.replace('/', '\/'))
    _replace_init_script_var('CODE_ROOT', env.code_root.replace('/', '\/'))
    _replace_init_script_var('VIRTUALENV_ROOT',
                             env.virtualenv_root.replace('/', '\/'))
    _replace_init_script_var('USER', env.user)


def restart_route():
    """
    Restarts the RapidSMS route process on the remote server.  Requires sudo
    permissions on /etc/init.d/mwana-route, e.g.:
    
    deployer ALL=NOPASSWD: ALL
    """
    # using run instead of sudo because sudo prompts for a password
    run('sudo supervisorctl restart mwana-router')
    # print out the top of the log file in case there are errors
    import time
    time.sleep(2)
    run('head -n 15 %s/route.log' % env.root)


def syncdb():
    """
    Runs ./manage.py syncdb on the remote server.
    """
    run('source %s/bin/activate' % env.virtualenv_root)
    run('%s/mwana/manage.py syncdb' % env.code_root)


def reset_local_db():
    """ Reset local database from remote host """
    require('root', provided_by=('production', 'staging'))
    question = 'Are you sure you want to reset your local ' \
               'database with the %(environment)s database?' % env
    if not console.confirm(question, default=False):
        utils.abort('Local database reset aborted.')
    if env.environment == 'staging-environment':
        from mwana.malawi.settings_staging import DATABASES as remote_dbs
    elif env.environment == 'production-environment':
        from mwana.malawi.settings_production import DATABASES as remote_dbs
    from mwana.localsettings import DATABASES as local_dbs
    remote_db = remote_dbs['default']['NAME']
    local_db = local_dbs['default']['NAME']
    with settings(warn_only=True):
        local('dropdb %s' % local_db)
    local('createdb %s' % local_db)
    host = '%s@%s' % (env.user, env.hosts[0])
    local('ssh -C %s pg_dump -Ox %s | psql %s' % (host, remote_db, local_db))


def bootstrap():
    """
    Bootstraps the remote server for the first time.  This is just a shortcut
    for the other more granular methods.
    """
    create_virtualenv()
    install_init_script()
    if not files.exists(env.code_root):
        clone_all()
        #deploy_from_local()
    pull_and_checkout_all()
    update_requirements()
    print '\nNow add your database password to localsettings.py and run syncdb'
