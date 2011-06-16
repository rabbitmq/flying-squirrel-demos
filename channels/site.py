#!/usr/bin/env python
from __future__ import with_statement

import os
import web
import random
import string
import flyingsquirrel as squirrel

from config import SERVICE_URL, SQUIRREL_SITE_URL

urls = (
    '/(index(.html)?)?', 'Channels'
)
app = web.application(urls, globals())

render = web.template.render('.')

class Channels:
    def GET(self, *_ignore):
        (conn_url, ticket) = create_endpoint()
        return render.index(SQUIRREL_SITE_URL, conn_url, ticket)

def create_endpoint():
    client = squirrel.API(SERVICE_URL)
    name = ''.join([random.choice(string.letters) for i in range(10)])
    endpoint = client.create_endpoint(
        name,
        definition={'pub': ['pub', name + '_pubsub'],
                    'sub': ['sub', name + '_pubsub'],
                    'push': ['push', name + '_pushpull'],
                    'pull': ['pull', name + '_pushpull'],
                    'req': ['req', name + '_reqrep'],
                    'rep': ['rep', name + '_reqrep']})
    ticket = client.generate_ticket(name, 'anon')
    return endpoint['protocols']['socket.io'], ticket

if __name__ == "__main__":
    if 'WSGI_DATA' not in os.environ:
        app.run()
    else:
        from flup.server.fcgi import WSGIServer

        from django.utils.daemonize import become_daemon
        become_daemon(out_log=os.environ['WSGI_DATA']+'/channels_out.log',
                      err_log=os.environ['WSGI_DATA']+'/channels_err.log')

        with open(os.environ['WSGI_DATA'] + "/channels.pid", "w") as f:
            f.write("%d\n" % os.getpid())

        web.config.debug = False

        WSGIServer(app.wsgifunc(),
                   bindAddress='/tmp/fs-channels.sock',
                   umask=0000).run()
