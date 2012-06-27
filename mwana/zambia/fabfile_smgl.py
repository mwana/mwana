"""
Server layout:
    ~/services/
        This contains two subfolders
            /apache/
            /supervisor/
        which hold the configurations for these applications
        for each environment (staging, demo, etc) running on the server.
        Theses folders are included in the global /etc/apache2 and
        /etc/supervisor configurations.

    ~/www/
        This folder contains the code, python environment, and logs
        for each environment (staging, demo, etc) running on the server.
        Each environment has its own subfolder named for its evironment
        (i.e. ~/www/staging/logs and ~/www/demo/logs).
"""
import os, sys
from fabric.api import *
from fabric.contrib import files, console
from fabric.contrib.files import uncomment
from fabric.contrib.files import exists
from fabric import utils
from fabric.decorators import hosts
import posixpath

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), '..')
env.home = '/home/mwana'
env.project = 'mwana'
env.code_repo = 'git@github.com:mwana/mwana.git'
env.country = 'zambia'
env.pip_requires_filename = 'from_www_libs.txt'
env.apache_ports = ['80']

def _setup_path():
    # using posixpath to ensure unix style slashes. See bug-ticket: http://code.fabfile.org/attachments/61/posixpath.patch
    env.root = posixpath.join(env.home, 'www', env.environment)
    env.log_dir = posixpath.join(env.home, 'www', env.environment, 'log')
    env.code_root = posixpath.join(env.root, 'code_root')
    env.project_root = posixpath.join(env.code_root, env.project)
    env.project_media = posixpath.join(env.code_root, 'media')
    env.project_static = posixpath.join(env.project_root, 'static')
    env.virtualenv_root = posixpath.join(env.root, 'python_env')
    env.services = posixpath.join(env.home, 'services')

def _set_apache_user():
    if what_os() == 'ubuntu':
       env.apache_user = 'www-data'
    elif what_os() == 'redhat':
        env.apache_user = 'apache'

def setup_dirs():
    """ create (if necessary) and make writable uploaded media, log, etc. directories """
    sudo('mkdir -p %(log_dir)s' % env, user=env.sudo_user)
    sudo('chmod a+w %(log_dir)s' % env, user=env.sudo_user)
    # sudo('mkdir -p %(project_media)s' % env, user=env.sudo_user)
    # sudo('chmod a+w %(project_media)s' % env, user=env.sudo_user)
    # sudo('mkdir -p %(project_static)s' % env, user=env.sudo_user)
    sudo('mkdir -p %(services)s/apache' % env, user=env.sudo_user)
    sudo('mkdir -p %(services)s/supervisor' % env, user=env.sudo_user)
    sudo('mkdir -p %(services)s/touchforms' % env, user=env.sudo_user)

def staging():
    """ use staging environment on remote host"""
    env.code_branch = 'develop'
    env.sudo_user = 'aremind'
    env.environment = 'staging'
    env.server_port = '9002'
    env.server_name = 'noneset'
    env.hosts = ['204.232.206.181']
    env.settings = '%(project)s.localsettings' % env
    env.remote_os = None
    env.db = '%s_%s' % (env.project, env.environment)
    _setup_path()

def production():
    """ use production environment on remote host"""
    env.code_branch = 'zhcard_dev'
    env.user = 'mwana'
    env.sudo_user = 'mwana'
    env.environment = 'production'
    env.apache_ports = ['80', '9005']
    env.server_port = '9001'
    env.server_name = 'smgl-production'
#    env.hosts = ['10.84.168.98']
#    env.hosts = ['173.203.221.48']
    env.hosts = ['41.191.116.75:9000']
    env.settings = '%(project)s.localsettings' % env
    env.remote_os = None # e.g. 'ubuntu' or 'redhat'.  Gets autopopulated by what_os() if you don't know what it is or don't want to specify.
    env.db = '%s_%s' % (env.project, env.environment)
    _setup_path()

def install_packages():
    """Install packages, given a list of package names"""
    require('environment', provided_by=('staging', 'production'))
    packages_list = ''
    installer_command = ''
    if what_os() == 'ubuntu':
        packages_list = 'apt-packages.txt'
        installer_command = 'apt-get install -y'
    elif what_os() == 'redhat':
        packages_list = 'yum-packages.txt'
        installer_command = 'yum install'
    packages_file = posixpath.join(PROJECT_ROOT, 'requirements', packages_list)
    with open(packages_file) as f:
        packages = f.readlines()
    sudo("%s %s" % (installer_command, " ".join(map(lambda x: x.strip('\n\r'), packages))))

def upgrade_packages():
    """
    Bring all the installed packages up to date.
    This is a bad idea in RedHat as it can lead to an
    OS Upgrade (e.g RHEL 5.1 to RHEL 6).
    Should be avoided.  Run install packages instead.
    """
    require('environment', provided_by=('staging', 'production'))
    if what_os() == 'ubuntu':
        sudo("apt-get update -y")
#        sudo("apt-get upgrade -y")
    else:
        return #disabled for RedHat (see docstring)

def what_os():
    with settings(warn_only=True):
        require('environment', provided_by=('staging','production'))
        if env.remote_os is None: #make sure we only run this check once per fab execution.
            print 'Testing operating system type...'
            if(files.exists('/etc/lsb-release',verbose=True) and files.contains(text='DISTRIB_ID=Ubuntu', filename='/etc/lsb-release')):
                env.remote_os = 'ubuntu'
                print 'Found lsb-release and contains "DISTRIB_ID=Ubuntu", this is an Ubuntu System.'
            elif(files.exists('/etc/redhat-release',verbose=True)):
                env.remote_os = 'redhat'
                print 'Found /etc/redhat-release, this is a RedHat system.'
            else:
                print 'System OS not recognized! Aborting.'
                exit()
        return env.remote_os

def setup_server():
    """Set up a server for the first time in preparation for deployments."""
    require('environment', provided_by=('staging', 'production'))
    upgrade_packages()
    # Install required system packages for deployment, plus some extras
    # Install pip, and use it to install virtualenv
    install_packages()
    create_db_user()
    create_db()

def create_db_user():
    """Create the Postgres user."""

    require('environment', provided_by=('staging', 'production'))
    sudo('createuser -D -A -R %(sudo_user)s' % env, user='postgres')

def create_db():
    """Create the Postgres database."""

    require('environment', provided_by=('staging', 'production'))
    sudo('createdb -O %(sudo_user)s %(db)s' % env, user='postgres')

def bootstrap():
    """ initialize remote host environment (virtualenv, deploy, update) """
    require('root', provided_by=('staging', 'production'))
    sudo('mkdir -p %(root)s' % env, user=env.sudo_user)
    clone_repo()
    setup_dirs()
    update_services()
    create_virtualenv()
    update_requirements()
    fix_locale_perms()

def create_virtualenv():
    """ setup virtualenv on remote host """
    require('virtualenv_root', provided_by=('staging', 'production'))
    with settings(warn_only=True):
        sudo('rm -rf %(virtualenv_root)s' % env, shell=False)
    args = '--clear --distribute'
    sudo('virtualenv %s %s' % (args, env.virtualenv_root), shell=False, user=env.sudo_user)

def clone_repo():
    """ clone a new copy of the git repository """
    with settings(warn_only=True):
        with cd(env.root):
            sudo('git clone %(code_repo)s %(code_root)s' % env, user=env.sudo_user)
            sudo('git checkout %(code_branch)s' % env, user=env.sudo_user)

def deploy():
    """ deploy code to remote host by checking out the latest via git """
    require('root', provided_by=('staging', 'production'))
    sudo('echo ping!') #hack/workaround for delayed console response
    if env.environment == 'production':
        if not console.confirm('Are you sure you want to deploy production?',
                               default=False):
            utils.abort('Production deployment aborted.')
    with settings(warn_only=True):
        stop()
    try:
        with cd(env.code_root):
            sudo('git checkout %(code_branch)s' % env, user=env.sudo_user)
#            sudo('git commit -am "Automatic server side commit (Translations)"', user=env.sudo_user) #commit any new translations
            sudo('git pull origin %(code_branch)s' % env, user=env.sudo_user)
            sudo('git submodule init', user=env.sudo_user)
            sudo('git submodule update', user=env.sudo_user)
#            sudo('git push origin %(code_branch)s' % env, user=env.sudo_user) #get any translations commits back up to
                                                                            #server. MAKE SURE ORIGIN IS WRITE ENABLED
#        update_requirements()
#        update_services()
        migrate()
        collectstatic()
        stop()
        upload_supervisor_conf()
        upload_apache_conf()
        touch()
    finally:
        # hopefully bring the server back to life if anything goes wrong
        start()

def update_requirements():
    """ update external dependencies on remote host """
    require('code_root', provided_by=('staging', 'production'))
    requirements = posixpath.join(env.code_root, 'mwana', 'requirements')
    with cd(requirements):
        cmd = ['pip install']
        cmd += ['-E %(virtualenv_root)s' % env]
        cmd += ['--requirement %s' % posixpath.join(requirements, env.pip_requires_filename)]
        sudo(' '.join(cmd), user=env.sudo_user)

def touch():
    """ touch apache and supervisor conf files to trigger reload. Also calls supervisorctl update to load latest supervisor.conf """
    require('code_root', provided_by=('staging', 'production'))
    apache_path = posixpath.join(posixpath.join(env.services, 'apache'), 'apache.conf')
    supervisor_path = posixpath.join(posixpath.join(env.services, 'supervisor'), 'supervisor.conf')
    sudo('touch %s' % apache_path, user=env.sudo_user)
    sudo('touch %s' % supervisor_path, user=env.sudo_user)
    _supervisor_command('update')

def update_services():
    """ upload changes to services such as nginx """

    with settings(warn_only=True):
        stop()
    upload_supervisor_conf()
    upload_apache_conf()
    start()
    netstat_plnt()

def configtest():
    """ test Apache configuration """
    require('root', provided_by=('staging', 'production'))
    run('apache2ctl configtest')

def apache_reload():
    """ reload Apache on remote host """
    require('root', provided_by=('staging', 'production'))
    if what_os() == 'redhat':
        sudo('/etc/init.d/httpd reload')
    elif what_os() == 'ubuntu':
        sudo('/etc/init.d/apache2 reload')

def apache_restart():
    """ restart Apache on remote host """
    require('root', provided_by=('staging', 'production'))
    sudo('/etc/init.d/apache2 restart')

def netstat_plnt():
    """ run netstat -plnt on a remote host """
    require('hosts', provided_by=('production', 'staging'))
    sudo('netstat -plnt')

def stop():
    """ stop server and celery on remote host """
    require('environment', provided_by=('staging', 'demo', 'production'))
    _supervisor_command('stop %(project)s:*' % env)

def start():
    """ start server and celery on remote host """
    require('environment', provided_by=('staging', 'demo', 'production'))
    _supervisor_command('start %(project)s:*' % env)

def servers_start():
    ''' Start the gunicorn servers '''
    require('environment', provided_by=('staging', 'demo', 'production'))
    _supervisor_command('start  %(project)s:server' % env)

def servers_stop():
    ''' Stop the gunicorn servers '''
    require('environment', provided_by=('staging', 'demo', 'production'))
    _supervisor_command('stop  %(project)s:server' % env)

def servers_restart():
    ''' Start the gunicorn servers '''
    require('environment', provided_by=('staging', 'demo', 'production'))
    _supervisor_command('restart  %(project)s:server' % env)

def migrate():
    """ run south migration on remote environment """
    require('project_root', provided_by=('production', 'demo', 'staging'))
    with cd(env.project_root):
        run('%(virtualenv_root)s/bin/python manage.py syncdb --noinput --settings=%(settings)s' % env)
        run('%(virtualenv_root)s/bin/python manage.py migrate --noinput --settings=%(settings)s' % env)

def collectstatic():
    """ run collectstatic on remote environment """
    require('project_root', provided_by=('production', 'demo', 'staging'))
    with cd(env.project_root):
        sudo('%(virtualenv_root)s/bin/python manage.py collectstatic --noinput --settings=%(settings)s' % env, user=env.sudo_user)

def reset_local_db():
    """ Reset local database from remote host """
    require('code_root', provided_by=('production', 'staging'))
    if env.environment == 'production':
        utils.abort('Local DB reset is for staging environment only')
    question = 'Are you sure you want to reset your local ' \
               'database with the %(environment)s database?' % env
    sys.path.append('.')
    if not console.confirm(question, default=False):
        utils.abort('Local database reset aborted.')
    if env.environment == 'staging':
        from aremind.settings_staging import DATABASES as remote
    else:
        from aremind.settings_production import DATABASES as remote
    from aremind.localsettings import DATABASES as loc
    local_db = loc['default']['NAME']
    remote_db = remote['default']['NAME']
    with settings(warn_only=True):
        local('dropdb %s' % local_db)
    local('createdb %s' % local_db)
    host = '%s@%s' % (env.user, env.hosts[0])
    local('ssh -C %s sudo -u aremind pg_dump -Ox %s | psql %s' % (host, remote_db, local_db))

def fix_locale_perms():
    """ Fix the permissions on the locale directory """
    require('root', provided_by=('staging', 'production'))
    _set_apache_user()
    locale_dir = '%s/aremind/locale/' % env.code_root
    sudo('chown -R %s %s' % (env.sudo_user, locale_dir), user=env.sudo_user)
    sudo('chgrp -R %s %s' % (env.apache_user, locale_dir), user='root')
    sudo('chmod -R g+w %s' % (locale_dir), user=env.sudo_user)

def commit_locale_changes():
    """ Commit locale changes on the remote server and pull them in locally """
    fix_locale_perms()
    with cd(env.code_root):
        sudo('-H -u %s git add aremind/locale' % env.sudo_user)
        sudo('-H -u %s git commit -m "updating translation"' % env.sudo_user)
    local('git pull ssh://%s%s' % (env.host, env.code_root))

def upload_supervisor_conf():
    """Upload and link Supervisor configuration from the template."""
    require('environment', provided_by=('staging', 'demo', 'production'))
    _set_apache_user()
    upload_dict = {}
    upload_dict["template"] = posixpath.join(os.path.dirname(__file__), 'services', 'templates', 'supervisor.conf')
    upload_dict["destination_tmp"] = '/var/tmp/supervisor.conf.blah'
    upload_dict["other_tmp"] = posixpath.join('/','var','tmp','supervisord.conf')
    upload_dict["services_destination"] =  posixpath.join(env.services, u'supervisor/supervisord.conf' % env)
    upload_dict["main_supervisor_conf_dir"] = '/etc'
    upload_dict["supervisor_search_path"] = posixpath.join(upload_dict["main_supervisor_conf_dir"], 'supervisord.conf')

    files.upload_template(upload_dict["template"], upload_dict["destination_tmp"], context=env, use_sudo=True)
    sudo('chown -R %s %s' % (env.sudo_user, upload_dict["destination_tmp"]))
    sudo('chgrp -R %s %s' % (env.apache_user, upload_dict["destination_tmp"]))
    sudo('chmod -R g+w %(destination_tmp)s' % upload_dict)
    sudo('mv -f %(destination_tmp)s %(services_destination)s' % upload_dict)
#    sudo('echo_supervisord_conf > %(supervisor_search_path)s' % upload_dict)
    #uncomment the include directive in supervisord.conf so we can point it to our supervisor conf
    uncomment(upload_dict["supervisor_search_path"], '\;\\[include\\]', use_sudo=True, char=';', backup='.bak')
    #update the line in the supervisord config file that points to our supervisor.conf
    #remove the line if it already exists
    sudo("sed '/.conf/d' %(supervisor_search_path)s > %(other_tmp)s" % upload_dict)
    #throw in the updated line
    sudo('echo "files = %(services_destination)s" >> %(other_tmp)s' % upload_dict )
    #move from other_tmp to the supervisor_search_path
    sudo('mv -f %(other_tmp)s %(supervisor_search_path)s' % upload_dict)
    _supervisor_command('update')

def upload_apache_conf():
    """Upload and link Supervisor configuration from the template."""
    require('environment', provided_by=('staging', 'demo', 'production'))
    _set_apache_user()
    template = posixpath.join(os.path.dirname(__file__), 'services', 'templates', 'apache.conf')
    destination = '/var/tmp/apache.conf.temp'
    port_string = " ".join(["*:%s" % p for p in env.apache_ports])
    env.apache_port_string = port_string
    files.upload_template(template, destination, context=env, use_sudo=True)
    enabled =  posixpath.join(env.services, u'apache/%(environment)s.conf' % env)
    sudo('chown -R %s %s' % (env.sudo_user, destination))
    sudo('chgrp -R %s %s' % (env.apache_user, destination))
    sudo('chmod -R g+w %s' % destination)
    sudo('mv -f %s %s' % (destination, enabled))
    if what_os() == 'ubuntu':
        sudo('a2enmod proxy')  #loaded by default in redhat
        sudo('a2enmod proxy_http') #loaded by default in redhat

    sites_enabled_dirfile = ''
    if what_os() == 'ubuntu':
        sites_enabled_dirfile = '/etc/apache2/sites-enabled/%(project)s.conf' % env
    elif what_os() == 'redhat':
        sites_enabled_dirfile = '/etc/httpd/conf.d/%(project)s.conf' % env
    with settings(warn_only=True):
        if files.exists(sites_enabled_dirfile):
            sudo('rm %s' % sites_enabled_dirfile)

    sudo('ln -s %s/apache/%s.conf %s' % (env.services, env.environment, sites_enabled_dirfile))
    apache_reload()

def _supervisor_command(command):
    require('hosts', provided_by=('staging', 'production'))
    sudo('supervisorctl %s' % command)
