from __future__ import with_statement
from fabric.api import *
from fabric.contrib.project import rsync_project
from contextlib import contextmanager as _contextmanager

# from fabric.contrib import django, files
# django.project('mud')
# from mud.core.models import Char

PREFIX = '/srv/fs-demos/mud'
DATA = '/srv/fs-demos-data'

@_contextmanager
def virtualenv():
    with prefix('source %s/venv/bin/activate' % PREFIX):
        yield

@_contextmanager
def mud():
    with virtualenv():
        with cd(PREFIX + '/mud'):
            yield

def flup_stop():
    with cd(DATA):
        run("kill `cat mud-django.pid` || true")

def flup_start():
    with virtualenv():
        with cd(PREFIX):
            run("./mud/manage.py runfcgi method=prefork socket=/tmp/fs-mud.sock pidfile=%(d)s/mud-django.pid outlog=%(d)s/mud-out.log errlog=%(d)s/mud-err.log daemonize=true workdir=%(p)s/mud umask=0000" % {'p':PREFIX, 'd':DATA})


def upload():
    for p in [PREFIX, DATA]:
        run('[ -e "%(p)s" ] || (sudo mkdir -p "%(p)s"; sudo chown ubuntu:ubuntu "%(p)s")' % {'p':p})
    rsync_project(
        remote_dir=PREFIX + '/..',
        exclude=['.hg', 'venv', "*.pyc"],
        delete=True)

    with cd(PREFIX):
        run('[ -e "venv" ] || virtualenv venv')
        with virtualenv():
            run('pip install -r requirements.txt')
        run('find . -name \*pyc|xargs --no-run-if-empty rm ')
    with mud():
        run('[ -e settings_local.py ] && rm settings_local.py')
        run('ln -s settings_local_prod.py settings_local.py')
        run('[ -e "/srv/fs-demos-data/mud.sqlite" ] || (./manage.py syncdb --noinput && ./manage.py loaddata core/rooms.json;)')


def deploy():
    upload()
    flup_stop()
    flup_start()


def clean():
    run('rm -rf %s/mud %s/mud.sqlite' % (PREFIX, DATA))

def prerequisites():
    sudo('apt-get -y install python-dev')

def install_erlang():
    put('install-erlang.sh', '/tmp')
    with cd('/usr/src'):
        sudo('bash /tmp/install-erlang.sh')

def setup_nginx():
    with cd('/etc/nginx/sites-enabled/'):
        run('[ -e mud.conf ] && sudo rm mud.conf ')
        sudo('ln -s %s/mud.conf' % PREFIX)
        sudo('/etc/init.d/nginx restart')

