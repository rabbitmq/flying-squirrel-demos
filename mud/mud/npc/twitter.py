import urllib
import httplib2
import json

from django.conf import settings

from mud.core import commands
from mud.core import models
from mud.core.signals import tick_event


H = httplib2.Http('.cache')
H.add_credentials(settings.IDENTICA_USER, settings.IDENTICA_PASS,
                  'identi.ca')

def identica_post(status):
    resp, content = H.request('https://identi.ca/api/statuses/update.json',
                              'POST',
                              urllib.urlencode({'status': status}),
                              headers={'Content-Type':
                                           'application/x-www-form-urlencoded'})
    try:
        assert resp['status'] == '200'
    except:
        print resp, content
        raise
    return json.loads(content)['id']


def bird():
    return models.Char.objects.get(nick__exact="Bird")


def got_tell(actor=None, target=None, text=None, **kwargs):
    try:
        tid = identica_post('%s: %s' % (actor, text))
    except Exception, e:
        commands._do_tell(target, actor, "I tell you nothing!")
        raise
    else:
        commands._do_say(target, "Tweet, tweet! (id=%s)" % (tid,))


def identica_mentions(since_id):
    resp, content = H.request('https://identi.ca/api/statuses/mentions.json?%s' %
                              (urllib.urlencode({'since_id': since_id}),),
                              'GET',
                              headers={'cache-control':'no-cache'})
    try:
        assert resp['status'] == '200'
    except:
        raise
    return list(reversed(json.loads(content)))

SINCEID=0
def poll_identica(sender, **kwargs):
    global SINCEID
    me = bird()
    last_sinceid = SINCEID
    messages = identica_mentions(SINCEID)
    if SINCEID == 0 and messages:
        messages = messages[-1]
    for msg in identica_mentions(SINCEID):
        SINCEID = msg['id']
        commands._do_say(me, "Bzz Bzz! %s: %s (%s)" %
                         (msg['user']['screen_name'], msg['text'], msg['id']))

tick_event.connect(poll_identica)
