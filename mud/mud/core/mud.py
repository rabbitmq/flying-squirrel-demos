from collections import defaultdict
from ..ordereddict import OrderedDict
from . import models

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
        actor.render('logo.txt')
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
    """ Say something within the room. """
    actor.render_to_others("say.txt", {'text':' '.join(args)})

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
    e = actor.room.exit(direction)
    if not e:
        actor.send("You can't go there.")
    else:
        do_move(actor, e, direction=direction)
        actor.save()

def do_move(actor, dst_room, direction=None):
    src_room = actor.room
    actor.render_to_others("bamf_out.txt", {'direction':direction})
    dst_room.render("bamf_in.txt", {'actor': actor, 'direction':direction})
    do_describe_room(actor, dst_room)
    actor.room = dst_room

def do_who(actor, **kwargs):
    """ Who's online? """
    actor.render('who.txt', {'chars': models.Char.online()})

def do_tell(actor, args=[], **kwargs):
    """ tell somebody something """
    if len(args) < 2:
        actor.send("What should I tell to who?")
        return
    try:
        target = models.Char.objects.get(nick__exact=args[0].capitalize())
    except models.Char.DoesNotExist:
        actor.send("Can't find " + args[0])
        return
    text = ' '.join(args[1:])
    target.render('tell.txt', {'actor':actor, 'text':text})
    target.reply = actor
    target.save()
    actor.reply = target
    actor.save()

def do_reply(actor, args=[], **kwargs):
    """ reply to a tell """
    if not actor.reply:
        actor.send("Who should I reply to?")
        return
    if len(args) < 1:
        actor.send("What should I tell %s about?" % (actor.reply,))
        return
    text = ' '.join(args)
    actor.reply.render('tell.txt', {'actor':actor, 'text':text})
    actor.reply.reply = actor
    actor.reply.save()

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
