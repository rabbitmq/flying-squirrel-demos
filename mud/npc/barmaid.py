from mud.core import commands, models
import random
from django.template.loader import render_to_string

def got_tell(actor=None, target=None, text='', **kwargs):
    order = text.split(' ')
    if len(order) > 0 and order[0] in ['beer', 'bitter', 'ale', 'lager']:
        actor.drunk += 3
        actor.save()
        actor.send(render_to_string('beer.txt', {}))
        commands._do_tell(target, actor,
                          "There you go, %s" %
                          random.choice(['pet', 'darlin', 'love', 'now get out.']))
    else:
        actor.send("The barmaid scans the rest of the bar for anyone actually wanting a drink")

