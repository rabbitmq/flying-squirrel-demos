import datetime

from django.shortcuts import render_to_response
from django.http import HttpResponseNotAllowed, HttpResponse, \
    HttpResponseNotFound
from . import fs
from . import signals


def index(request):
    if request.method == 'GET':
        return index_get(request)
    elif request.method == 'POST':
        return index_post(request)
    else:
        return HttpResponseNotAllowed(['GET', 'POST'])

def index_get(request):
    identity, transport_url, ticket = fs.client_ticket()
    my_context = {
        'identity': identity,
        'transport_url': transport_url,
        'ticket': ticket,
        }
    return render_to_response('index.html', my_context)

def index_post(request):
    headers = dict((k[5:].lower().replace('_', '-'), v)
                   for k, v in request.META.iteritems()
                   if k.startswith('HTTP_'))
    #print request.raw_post_data, headers
    status = fs.webhooks_client.deliver_message(request.raw_post_data, headers)

    if status in [200, 204]:
        return HttpResponse('ok')
    elif status in [404]:
        return HttpResponseNotFound()
    return HttpResponse(status=status)



def tick(request):
    signals.tick_event.send(sender=request,
                            curr_time=datetime.datetime.now())
    fs.flush()
    return HttpResponse('ok')
