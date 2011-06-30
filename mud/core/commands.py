from .ordereddict import OrderedDict
from . import models
from . import trigger
import random

SPINNING = 2
STAGGERING = 4
SLURRING = 6

def do_help(actor, args=None, **kwargs):
    """ Print this help. """
    funs = []
    for cmd, fun in [(cmd, COMMANDS[cmd]) for cmd in COMMANDS.keys()]:
        if isinstance(fun, tuple):
            fun, user_kwa = fun
        funs.append( (cmd, fun.__doc__) )
    actor.render("help.txt", {'funs':funs})

def do_say(actor, args=None, **kwargs):
    """ Say something within the room. """
    speech = args
    if actor.drunk > SLURRING:
        jumble(speech, actor.drunk - SLURRING)
    _do_say(actor, ' '.join(speech))

def jumble(words, swaps):
    if swaps <= 0:
        return
    ind = random.randint(1, len(words) - 1)
    s = words[ind]
    words[ind] = words[ind-1]
    words[ind-1] = s
    jumble(words, swaps - 1)

def _do_say(actor, text):
    actor.render("say_to.txt", {'text':text})
    actor.render_to_others("say.txt", {'text': text})

    trigger.action('say', actor=actor, text=text)
    for target in actor.others_in_room():
        trigger.action('someone_said', actor=actor, target=target, text=text)


def do_shout(actor, args=None, **kwargs):
    """ Shout to everyone. """
    models.Char.broadcast("shout.txt", {'actor': actor, 'text':' '.join(args)})


def do_describe_room(actor, room):
    actor.render('room.txt', {'room': room})

def do_look(actor, args=[], **kwargs):
    """ Describe what's around you. """
    room = None
    if len(args) == 0:
        do_describe_room(actor, actor.room)
        return

    what = args[0]
    room = actor.room.exit(what)
    if room is not None:
        actor.render('room_brief.txt', {'room': room})
        return
    try:
        target = actor.room.char_set.get(nick__exact=what.capitalize())
    except models.Char.DoesNotExist:
        target = None
    if target:
        actor.room.render("stare.txt", {'actor':actor, 'target': target}, skip=[actor, target])
        target.render("stare_at_you.txt", {'actor': actor})
        actor.render("look_at_char.txt", {'target': target})
    else:
        actor.send("You see nothing there.")

def do_go(actor, direction=None, **kwargs):
    """ Go in a direction. """
    if actor.drunk >= STAGGERING:
        actor.render("stagger.txt")
        e = random.choice(actor.room.exits.all()).dst
        _do_move(actor, e, direction=direction,
                 bamf_in="stagger_in.txt", bamf_out="stagger_out.txt")
    else:
        e = actor.room.exit(direction)
        if not e:
            actor.send("You can't go there.")
            return actor
        else:
            _do_move(actor, e, direction=direction)
    if actor.drunk > 0: actor.drunk -= 1
    actor.save()

def _do_move(actor, dst_room, direction=None,
             bamf_in="bamf_in.txt", bamf_out="bamf_out.txt"):
    src_room = actor.room
    actor.render_to_others(bamf_out, {'direction':direction})
    dst_room.render(bamf_in, {'actor': actor, 'direction':direction})
    do_describe_room(actor, dst_room)
    actor.room = dst_room

def do_who(actor, **kwargs):
    """ Who's online? """
    actor.render('who.txt', {'chars': models.Char.online()})

def _do_tell(actor, target, text):
    if not text:
        actor.send("What should I tell %s about?" % (target,))
        return
    if not target:
        actor.send("Who should I tell it?")
        return
    if target.connected() == 0:
        actor.send("I don't think %s can hear you now." % (target,))
        return
    target.reply = actor
    target.save()
    actor.reply = target
    actor.save()
    target.render('tell.txt', {'actor':actor, 'text':text})
    actor.render('tell_to.txt', {'target':target, 'text':text})
    trigger.action('tell', actor=actor, target=target, text=text)

def do_tell(actor, args=[], **kwargs):
    """ Tell somebody something. """
    if len(args) < 2:
        actor.send("What should I tell to who?")
        return
    try:
        target = models.Char.objects.get(nick__exact=args[0].capitalize())
    except models.Char.DoesNotExist:
        actor.send("Can't find " + args[0])
        return
    _do_tell(actor, target, ' '.join(args[1:]))

def do_reply(actor, args=[], **kwargs):
    """ Reply to a tell. """
    _do_tell(actor, actor.reply, ' '.join(args))


COMMANDS=OrderedDict([
    ('help', do_help),
    ('say', do_say),
    ('shout', do_shout),
    ('look', do_look),
    ('who', do_who),
    ('tell', do_tell),
    ('reply', do_reply),
    ('n', (do_go, {'direction': 'n'})),
    ('e', (do_go, {'direction': 'e'})),
    ('w', (do_go, {'direction': 'w'})),
    ('s', (do_go, {'direction': 's'})),
])
