#!/usr/bin/env python

import random
import string
import web
import flyingsquirrel as squirrel

from config import SERVICE_URL


urls = (
    '/(index(.html)?)?', 'Cursors'
)
app = web.application(urls, globals())

render = web.template.render('.')

class Cursors:
    def GET(self, *_ignore):
        username, transport_url, ticket = create_endpoint()
        return render.index(username, transport_url, ticket)

def create_endpoint():
    client = squirrel.API(SERVICE_URL)
    endpoint = client.create_endpoint(
        "flying_cursors",
        definition = {'egress': ['pub', 'flying_cursors'],
                      'ingress': ['sub', 'flying_cursors']})
    username = ''.join(random.choice(string.letters) for i in xrange(8))
    ticket = client.generate_ticket('flying_cursors', username)
    return (username, endpoint['protocols']['socket.io'], ticket)

if __name__ == "__main__":
    app.run()
