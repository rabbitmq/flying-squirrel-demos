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

    def render(self, tname, ctx={}):
        c = {'room':self}
        c.update(ctx)
        data = render_to_string(tname, c).strip()
        for char in self.char_set.all():
            char._raw_send(data)

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

    modified = models.DateField(auto_now=True)
    nick = models.CharField(max_length=32)
    room = models.ForeignKey(Room)

    def render(self, tname, ctx={}):
        c = {'actor':self, 'room':self.room}
        c.update(ctx)
        self._raw_send(render_to_string(tname, c).strip())

    def send(self, msg):
        return self.render('_default.txt', {'text': msg})

    def _raw_send(self, raw_msg):
        for conn in self.connection_set.all():
            conn.send(raw_msg)

    def render_to_others(self, tname, ctx={}):
        c = {'actor':self, 'room':self.room}
        c.update(ctx)
        data = render_to_string(tname, c).strip()
        for ch in self.room.char_set.all():
            if ch == self:
                pass
            else:
                ch._raw_send(data)

    @classmethod
    def online(cls):
        return cls.objects.filter(connection__reply_to__isnull=False).distinct()

    @classmethod
    def broadcast(cls, tname, ctx, skip=None):
        data = render_to_string(tname, ctx).strip()
        for ch in cls.online():
            if ch != skip:
                ch._raw_send(data)

class Connection(models.Model):
    def __unicode__(self):
        return "%s --> %s" % (self.reply_to, self.char)

    modified = models.DateTimeField(auto_now=True)
    reply_to = models.CharField(max_length=32)
    char = models.ForeignKey(Char, null=True)
    state = models.CharField(max_length=16, default="connected")

    def send(self, msg):
        _outbound(self.reply_to, msg)


OUTBOUND={}
def _outbound(reply_to, message):
    OUTBOUND.setdefault(reply_to, []).append(message)
