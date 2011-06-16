import random

from mud.core import commands
from mud.core import models

from django.template.loader import render_to_string

lines = render_to_string('_lines.txt', {}).split('\n')

def probability(n):
    return bool(random.randrange(0, 100) < n)

def prompter():
    return models.Char.objects.get(nick__exact="Prompter")

def got_tell(actor=None, target=None, text='', **kwargs):
    if text == 'line' or text == 'line?':
        line = random.choice(lines)
        commands._do_tell(target, actor, '"%s"' % (line,))
    else:
        actor.send("%s arches his eyebrow expectantly" % (prompter(),))

def got_someone_said(actor=None, **kwargs):
    me = prompter()
    if actor != me:
        commands._do_say(me, "That's not the line! Get off the stage!" )
        if probability(20):
            actor.send("You feel a hard kick from %s on your back." %(me,))
            actor.send_to_others("%s kicks %s off the stage." % (me, actor))
            commands.do_go(actor,  'e')

