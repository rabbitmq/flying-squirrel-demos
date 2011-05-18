#!/usr/bin/env python

import web
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
    endpoint = client.create_endpoint(
        'fixme',
        definition={'pub': ['pub', 'fixme_pubsub'],
                    'sub': ['sub', 'fixme_pubsub'],
                    'push': ['push', 'fixme_pushpull'],
                    'pull': ['pull', 'fixme_pushpull'],
                    'req': ['req', 'fixme_reqrep'],
                    'rep': ['rep', 'fixme_reqrep']})
    ticket = client.generate_ticket('fixme', 'fixme')
    return endpoint['protocols']['socket.io'], ticket

if __name__ == "__main__":
    app.run()
