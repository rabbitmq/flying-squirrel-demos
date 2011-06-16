from __future__ import with_statement
from fabric.api import *
from fabric.contrib.project import rsync_project
from contextlib import contextmanager as _contextmanager

# The trailing folder must be 'flying-squirrel-demos'.
PREFIX = '/srv/flying-squirrel-demos'
DATA   = '/srv/flying-squirrel-data'


@_contextmanager
def virtualenv():
    with prefix('source %s/venv/bin/activate' % PREFIX):
        yield


def upload():
    for p in [PREFIX, DATA]:
        run('[ -e "%(p)s" ] || (sudo mkdir -p "%(p)s"; sudo chown ubuntu:ubuntu "%(p)s")' % {'p':p})
    run('sudo chown -R srs:srs %s' % (DATA,))
    run('sudo chmod 777 %s' % (DATA,))

    rsync_project(
        remote_dir=PREFIX + '/..',
        exclude=['.hg', 'venv', "*.pyc"],
        delete=True)

    with cd(PREFIX):
        run('[ -e "venv" ] || virtualenv venv')
        with virtualenv():
            run('pip install -r requirements.txt')
            run('python -m compileall -q .')

def prerequisites():
    sudo('apt-get -y install python-dev')


def mud_setup():
    with virtualenv():
        with cd(PREFIX + '/mud'):
            run('[ -e settings_local.py ] && rm settings_local.py || true')
            run('ln -s settings_local_prod.py settings_local.py')
            run('[ -e "'+DATA+'/mud.sqlite" ] || (./manage.py syncdb --noinput && ./manage.py loaddata core/rooms.json;)')
    run('sudo chown srs:srs %s/mud.sqlite' % (DATA,))
    with cd('/etc/nginx/sites-enabled/'):
        # run('[ -e srs ] && sudo rm srs || true')
        run('[ -e 00-mud.conf ] && sudo rm 00-mud.conf || true')
        sudo('ln -s %s/mud.conf 00-mud.conf' % (PREFIX,))
        sudo('/etc/init.d/nginx restart')
    run('sudo crontab -u srs %(p)s/crontab' %  {'p':PREFIX,})

def mud_stop():
    with cd(DATA):
        run("sudo -u srs kill `cat mud.pid` || true")

def mud_start():
    with virtualenv():
        with cd(PREFIX + '/mud'):
            run("sudo -u srs %(p)s/venv/bin/python ./manage.py runfcgi method=prefork socket=/tmp/fs-mud.sock pidfile=%(d)s/mud.pid outlog=%(d)s/mud-out.log errlog=%(d)s/mud-err.log daemonize=true workdir=%(p)s/mud umask=0000" % {'p':PREFIX, 'd':DATA})


def channels_setup():
    with cd('/etc/nginx/sites-enabled/'):
        # run('[ -e srs ] && sudo rm srs || true')
        run('[ -e 00-channels.conf ] && sudo rm 00-channels.conf || true')
        sudo('ln -s %s/channels.conf 00-channels.conf' % (PREFIX,))
        sudo('/etc/init.d/nginx restart')

def channels_stop():
    with cd(DATA):
        run("sudo -u srs kill `cat channels.pid` || true")

def channels_start():
    with virtualenv():
        with cd(PREFIX + '/channels'):
            run("sudo -u srs PYTHONPATH='%(d)s' %(p)s/venv/bin/python ../run.py %(d)s channels" % {'p': PREFIX, 'd':DATA})


def deploy():
    upload()
    mud_setup()
    mud_stop()
    mud_start()
    channels_setup()
    channels_stop()
    channels_start()

