from collections import defaultdict
from ..ordereddict import OrderedDict
from . import models
from django.template.loader import render_to_string

def inbound(conn, msg):
    if conn.state == 'connected':
        conn.send('Connected!')
        conn.send('Enter your nick:')
        conn.state = "username"
        conn.save()
    elif conn.state == 'username':
        nick = msg.capitalize()
        try:
            actor = models.Char.objects.get(nick__exact=nick)
        except models.Char.DoesNotExist:
            actor = models.Char(nick=nick, room_id=1)
        actor.save()
        conn.char = actor
        conn.state = "commands"
        conn.save()
        actor.send(render_to_string('logo.txt', {'actor': actor}))
        if actor.room_id == 1:
            do_move(actor, models.Room.objects.get(id__exact=2))
            actor.save()
        else:
            do_look(actor)
    elif conn.state == 'commands':
        actor = conn.char
        actor.send("> " + msg)
        cmd, _, args = msg.partition(' ')
        cmd, args = cmd.lower(), args.split()
        if cmd in COMMANDS:
            fun = COMMANDS[cmd]
            if isinstance(fun, tuple):
                fun, user_kwa = fun
            else:
                user_kwa = {}
            kwa = {'connection':conn, 'command':cmd, 'args':args}
            kwa.update(user_kwa)
            fun(actor, **kwa)
        else:
            actor.send("Unknown command. Type 'help' to see help.")
    else:
        assert False, conn.state


def do_help(actor, args=None, **kwargs):
    """ Print this help. """
    funs = []
    for cmd, fun in [(cmd, COMMANDS[cmd]) for cmd in COMMANDS.keys()]:
        if isinstance(fun, tuple):
            fun, user_kwa = fun
        funs.append( (cmd, fun.__doc__) )
    actor.render("help.txt", {'funs':funs})

def do_say(actor, args=None, **kwargs):
    """ Say something. """
    msg = "%s says: %s" % (actor.nick, ' '.join(args))
    for target in models.Char.objects.all():
        target.send(msg)

def do_look(actor, room=None, args=[], **kwargs):
    """ Describe what's around you. """
    if not room and len(args) == 1:
        e = actor.room.exit(args[0])
        if e:
            room = e

    if room is None:
        room = actor.room
    actor.send(render_to_string('room.txt', {'actor': actor,
                                             'room': room}))

def do_go(actor, direction=None, **kwargs):
    e = actor.room.exit(direction)
    if not e:
        actor.send("You can't go there.")
    else:
        do_move(actor, e.dst, direction=direction)
        actor.save()

def do_move(actor, dst_room, direction=None):
    src_room = actor.room
    actor.render_to_others("bamf_out.txt", {'direction':direction})
    dst_room.render("bamf_in.txt", {'actor': actor, 'direction':direction})
    do_look(actor, room=dst_room)
    actor.room = dst_room

def do_who(actor, **kwargs):
    """ Who's online? """
    actor.render('who.txt', {'chars': models.Char.online()})

COMMANDS=OrderedDict([
    ('help', do_help),
    ('say', do_say),
    ('look', do_look),
    ('who', do_who),
    ('n', (do_go, {'direction': 'n'})),
    ('e', (do_go, {'direction': 'e'})),
    ('w', (do_go, {'direction': 'w'})),
    ('s', (do_go, {'direction': 's'})),
])
