import random

from mud.core import commands
from mud.core import models


def probability(n):
    return bool(random.randrange(0, 100) < n)

def prompter():
    return models.Char.objects.get(nick__exact="Prompter")

def got_tell(actor=None, target=None, **kwargs):
    commands._do_tell(target, actor, "fuck off")

def got_someone_said(actor=None, **kwargs):
    me = prompter()
    if actor != me:
        commands._do_say(me, "Shut up! And get off the stage!" )
        if probability(70):
            actor.send("You feel a hard kick from %s on your back." %(me,))
            actor.send_to_others("%s kicks %s off the stage." % (me, actor))
            commands.do_go(actor,  'e')

