SERVICE_URL='http://guest:guest@localhost:55670/socks-api/default'

import random
import string
import web
import web.contrib.template
import flyingsquirrel as squirrel

import mud

import threading
import Queue

OUTBOX=Queue.Queue()

class Worker(threading.Thread):
    def run(self):
        while True:
            (channel, reply_to, message) = OUTBOX.get()
            webhooks_client.publish(channel, message,
                                    {'reply-to': reply_to})

worker = Worker()
worker.start()



randstr = lambda: ''.join(random.choice(string.letters) for i in xrange(8))


urls = (
    '/(index(.html)?)?', 'Cursors'
)
app = web.application(urls, globals())

render = web.contrib.template.render_mako(directories=['.'])

class Cursors:
    def GET(self, *_ignore):
        identity, transport_url, ticket = client_ticket()
        return render.index(identity=identity,
                            transport_url=transport_url,
                            ticket=ticket)

    def POST(self, *_ignore):
        headers = dict((k[5:].lower().replace('_', '-'), v)
                       for k, v in web.ctx.environ.iteritems()
                       if k.startswith('HTTP_'))

        status = webhooks_client.deliver_message(web.data(), headers)
        web.header('connection', 'close')
        if status in [200, 204]:
            return web.OK()
        elif status in [404]:
            return web.notfound()
        else:
            return web.HTTPError(status=status)


mud_world = mud.MudWorld()

CONNECTIONS=set()
def inbound_messages(msg, channel=None, msgobj=None, **kwargs):
    reply_to = msgobj['reply-to']
    if reply_to not in CONNECTIONS:
        CONNECTIONS.add(reply_to)
        mud_world.connected(reply_to, msg)
    else:
        mud_world.inbound(reply_to, msg)

    for reply_to, messages in mud_world.outgoing():
        OUTBOX.put( (channel, reply_to, '\n\r'.join(messages)) )

api = None
transport_socket_io = None
webhooks_client = None

def safe_endpoint(name, definition):
    # Delete endpoint only if absolutely required.
    try:
        endpoint = api.create_endpoint(name, definition=definition)
    except squirrel.HttpError:
        try:
            api.delete_endpoint(endpoint)
        except squirrel.HttpError:
            pass
        endpoint = api.create_endpoint(name, definition=definition)
    return endpoint

def prepare():
    global api, transport_socket_io, webhooks_client
    api = squirrel.API(SERVICE_URL)

    endpoint = safe_endpoint("mud_server", {'world': ['pub', 'world'],
                                            'pipe': ['rep', 'mesh']})

    transport_webhooks = endpoint['protocols']['webhooks']
    ticket = api.generate_ticket('mud_server', 'mr. server', timeout=9999999999)

    webhooks_client = squirrel.WebHooksClient(transport_webhooks, ticket,
                                              'http://localhost:8080/')
    webhooks_client.subscribe('pipe', inbound_messages)

    endpoint = safe_endpoint("mud_client", {'world': ['sub', 'world'],
                                            'pipe': ['req', 'mesh']})
    transport_socket_io = endpoint['protocols']['socket.io']


def client_ticket():
    identity = randstr()

    ticket = api.generate_ticket('mud_client', identity)
    return (identity, transport_socket_io, ticket)

if __name__ == "__main__":
    prepare()
    app.run()
