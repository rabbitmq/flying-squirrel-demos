from django.conf import settings
import logging
log = logging.getLogger(__name__)

import flyingsquirrel as squirrel

from . import utils
from . import models
from . import mud

api = None
transport_socket_io = None
webhooks_client = None

def safe_create_endpoint(name, definition):
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
    log.info(" [fs] preparing endpoints")
    global api, transport_socket_io, webhooks_client
    api = squirrel.API(settings.SQUIRRUS_URL)

    endpoint = safe_create_endpoint("mud_server", {'world': ['pub', 'world'],
                                                   'pipe': ['rep', 'mesh']})

    transport_webhooks = endpoint['protocols']['webhooks']
    ticket = api.generate_ticket('mud_server', 'mr. server', timeout=9999999999)

    webhooks_client = squirrel.WebHooksClient(transport_webhooks, ticket,
                                              settings.SQUIRRUS_LOCAL_URL)
    webhooks_client.subscribe('pipe', inbound_messages)

    endpoint = safe_create_endpoint("mud_client", {'world': ['sub', 'world'],
                                                   'pipe': ['req', 'mesh']})
    transport_socket_io = endpoint['protocols']['socket.io']
    log.info(" [fs] ok")

def client_ticket():
    identity = utils.randstr(8)

    ticket = api.generate_ticket('mud_client', identity)
    return (identity, transport_socket_io, ticket)


def inbound_messages(msg, channel=None, msgobj=None, **kwargs):
    reply_to = msgobj['reply-to']
    try:
        conn = models.Connection.objects.get(reply_to__exact=reply_to)
    except models.Connection.DoesNotExist:
        conn = models.Connection(reply_to=reply_to)
    conn.save()
    mud.inbound(conn, msg)
    flush()

def flush():
    for reply_to, messages in models.OUTBOUND.iteritems():
        webhooks_client.publish('pipe', '\n\r'.join(messages),
                                {'reply-to': reply_to})
    models.OUTBOUND.clear()
