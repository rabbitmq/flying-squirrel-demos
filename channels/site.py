#!/usr/bin/env python

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
    app.run()
