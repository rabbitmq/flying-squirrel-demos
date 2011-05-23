import sys
from collections import defaultdict

def do_help(actor, args=None, **kwargs):
    """ Print this help. """
    actor.send('Available commands:')
    for cmd, fun in [(cmd, COMMANDS[cmd]) for cmd in sorted(COMMANDS.keys())]:
        actor.send( ' %10s : %s' % (cmd, fun.__doc__))

def do_say(actor, args=None, **kwargs):
    """ Say something. """
    msg = "%s says: %s" % (actor.nick, ' '.join(args))
    for target_nick in USERS:
        user_by_nick(target_nick).send(msg)


COMMANDS={
    'help': do_help,
    'say': do_say,
}

CONNECTIONS={}
def connection_by_identity(identity):
    return CONNECTIONS.get(identity, None)

class Connection(object):
    def __init__(self, identity):
        self.identity = identity
        CONNECTIONS[identity] = self

        send_to_connection(identity, "Connected!")
        send_to_connection(identity, "Enter your nick:")
        self.inbound = self._state_wait_for_nick

    def _state_wait_for_nick(self, nick):
        nick = nick.capitalize()
        send_to_connection(self.identity, "Hello %s!" % (nick,))
        send_to_connection(self.identity, "Type 'help' to see help.")
        self.nick = nick
        actor = user_by_nick(nick)
        actor.connections.add(self.identity)
        actor.save()
        self.inbound = self._state_wait_for_command

    def _state_wait_for_command(self, line):
        actor = user_by_nick(self.nick)
        actor.send("> " + line)
        cmd, _, args = line.partition(' ')
        cmd, args = cmd.lower(), args.split()

        if cmd in COMMANDS:
            COMMANDS[cmd](actor, connection=self, command=cmd, args=args)
        else:
            actor.send("Unknown command. Type 'help' to see help.")

    def save(self):
        pass


USERS={}
def user_by_nick(nick):
    u = USERS.get(nick, None)
    if not u:
        u = User(nick)
    return u

class User(object):
    def __init__(self, nick):
        self.nick = nick
        USERS[nick] = self
        self.connections = set()

    def send(self, message):
        for identity in self.connections:
            send_to_connection(identity, message)

    def save(self):
        pass



send_to_connection = None

class MudWorld(object):
    def __init__(self):
        # identity -> [message]
        self._outgoing = defaultdict(list)

        global send_to_user, send_to_connection
        send_to_connection = self.send_to_connection

    def connected(self, identity, message):
        c = Connection(identity)
        c.save()

    def inbound(self, identity, message):
        c = connection_by_identity(identity)
        if c:
            c.inbound(message)
        else:
            print "Can't find user ", identity

    def send_to_connection(self, identity, message):
        self._outgoing[identity].append(message)

    def outgoing(self):
        r = self._outgoing.items()
        self._outgoing.clear()
        return r
