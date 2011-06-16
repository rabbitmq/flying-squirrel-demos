#!/usr/bin/env python
from __future__ import with_statement
import os
import sys

import web
from flup.server.fcgi import WSGIServer
from django.utils.daemonize import become_daemon
from django.utils.importlib import import_module


data_dir = sys.argv[1]
name = sys.argv[2]

become_daemon(out_log=data_dir + '/' + name + '_out.log',
              err_log=data_dir + '/' + name + '_err.log')

with open(data_dir + '/' + name + '.pid', "w") as f:
    f.write("%d\n" % os.getpid())

web.config.debug = False

app = import_module(name + '.site').app

WSGIServer(app.wsgifunc(),
           bindAddress='/tmp/fs-' + name +'.sock',
           umask=0000).run()
