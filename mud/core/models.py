from django.db import models
from django.template.loader import render_to_string

class Room(models.Model):
    def __unicode__(self):
        return "%s" % (self.name,)
    name = models.CharField(max_length=80)
    description = models.TextField()

    def send(self, msg):
        for char in self.char_set.all():
            char.send(msg)

    def render(self, tname, ctx={}, skip=[]):
        c = {'room':self}
        c.update(ctx)
        data = render_to_string(tname, c).strip()
        for ch in self.char_set.all():
            if ch not in skip:
                ch._raw_send(data)

    def exit(self, direction):
        try:
            return self.exits.get(keyword__exact=direction).dst
        except Exit.DoesNotExist:
            return None



class Exit(models.Model):
    def __unicode__(self):
        return "%s --%s--> %s" % (self.src, self.keyword, self.dst)

    keyword = models.CharField(max_length=32)
    src = models.ForeignKey(Room, related_name='exits')
    dst = models.ForeignKey(Room, related_name='entries')


class Char(models.Model):
    def __unicode__(self):
        return "%s" % (self.nick,)

    modified = models.DateTimeField(auto_now=True)
    nick = models.CharField(max_length=32)
    room = models.ForeignKey(Room)
    reply = models.ForeignKey("self", null=True, blank=True)
    is_npc = models.BooleanField(default=False)
    drunk = models.IntegerField(default=0)

    description = models.TextField()

    def render(self, tname, ctx={}):
        c = {'actor':self, 'room':self.room}
        c.update(ctx)
        self._raw_send(render_to_string(tname, c).strip())

    def send(self, msg):
        self.render('_default.txt', {'text': msg})

    def send_to_others(self, msg):
        data = render_to_string('_default.txt', {'actor': self, 'text': msg}).strip()
        for ch in self.others_in_room():
            ch._raw_send(data)

    def _raw_send(self, raw_msg):
        for conn in self.connection_set.all():
            conn.send(raw_msg)

    def render_to_others(self, tname, ctx={}):
        c = {'actor':self, 'room':self.room}
        c.update(ctx)
        data = render_to_string(tname, c).strip()
        for ch in self.others_in_room():
            ch._raw_send(data)

    def others_in_room(self):
        for ch in self.room.char_set.all():
            if ch != self:
                yield ch

    @classmethod
    def online(cls):
        return cls.objects.filter(connection__reply_to__isnull=False).distinct()

    @classmethod
    def broadcast(cls, tname, ctx, skip=[]):
        data = render_to_string(tname, ctx).strip()
        for ch in cls.online():
            if ch not in skip:
                ch._raw_send(data)

    def connected(self):
        if self.is_npc:
            return True
        return self.connection_set.count() > 0


class Npc(models.Model):
    def __unicode__(self):
        return "[%s]" % (self.char,)

    codepath = models.CharField(max_length=128)
    char = models.OneToOneField(Char)


class Connection(models.Model):
    def __unicode__(self):
        return "%s --> %s" % (self.reply_to, self.char)

    modified = models.DateTimeField(auto_now=True)
    reply_to = models.CharField(max_length=32)
    char = models.ForeignKey(Char, null=True)
    state = models.CharField(max_length=16, default="connected")

    def send(self, msg):
        _outbound(self.reply_to, msg)

    def render(self, tname, ctx={}):
        c = {'connection':self}
        c.update(ctx)
        self.send(render_to_string(tname, c).strip())


OUTBOUND={}
def _outbound(reply_to, message):
    OUTBOUND.setdefault(reply_to, []).append(message)
