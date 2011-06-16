import logging
log = logging.getLogger(__name__)

import datetime
import django.dispatch
from . import models
from . import trigger


tick_event = django.dispatch.Signal(providing_args=["curr_time"])


def cleanup_connections(sender, curr_time=None, **kwargs):
    t0 = curr_time - datetime.timedelta(seconds = 60)
    for conn in models.Connection.objects.filter(modified__lt=t0):
        actor = conn.char
        log.info(" [*] %s (%s) disconnected", actor, conn.reply_to)
        conn.send("Come back to us later.")
        conn.send("Disconnected...")
        conn.delete()

        if actor and not actor.is_npc and actor.connection_set.count() == 0:
            # Last connection lost, moving to limbo
            actor.render_to_others('to_limbo.txt')
            actor.room_id = 1
            actor.save()


tick_event.connect(cleanup_connections)


# Load all npc modules.
def load_npc():
    for actor in models.Char.objects.filter(is_npc=True):
        trigger.action('load', actor=actor)

load_npc()
