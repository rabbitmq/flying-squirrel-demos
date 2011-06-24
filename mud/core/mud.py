import string

from . import models
from . import commands

def inbound(conn, msg):
    if conn.state == 'connected':
        conn.send('Connected!')
        conn.send('Enter your nick:')
        conn.state = "username"
        conn.save()
    elif conn.state == 'username':
        nick = filter(lambda c: c in string.letters, msg).capitalize()
        if not nick:
            conn.state = "connected"
            return inbound(conn, '')
        try:
            actor = models.Char.objects.get(nick__exact=nick)
        except models.Char.DoesNotExist:
            actor = models.Char(nick=nick, room_id=1)
        actor.save()
        conn.render('logo.txt', {'actor':actor})
        conn.char = actor
        if not actor.is_npc:
            conn.state = "commands"
        else:
            conn.state = "listen"
        conn.save()
        if actor.room_id == 1:
            commands._do_move(actor, models.Room.objects.get(id__exact=2))
            actor.save()
        else:
            commands.do_look(actor)
    elif conn.state == 'commands':
        actor = conn.char
        actor.send("> " + msg)
        cmd, _, args = msg.partition(' ')
        cmd, args = cmd.lower(), args.split()
        if cmd in commands.COMMANDS:
            fun = commands.COMMANDS[cmd]
            if isinstance(fun, tuple):
                fun, user_kwa = fun
            else:
                user_kwa = {}
            kwa = {'connection':conn, 'command':cmd, 'args':args}
            kwa.update(user_kwa)
            fun(actor, **kwa)
        else:
            actor.send("Unknown command. Type 'help' to see help.")
    elif conn.state == 'listen':
        pass
    else:
        assert False, conn.state


