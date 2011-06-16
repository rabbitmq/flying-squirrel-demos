import logging
log = logging.getLogger(__name__)

from django.utils.importlib import import_module

from . import actions

def _run_cb(module, action, kwargs):
    if hasattr(module, action):
        try:
            getattr(module, action)(**kwargs)
        except Exception, e:
            log.error("Error on calling %s.%s",
                      module, action, exc_info=True)

def _run_fun(actor, action, kwargs):
    if actor.is_npc:
        if not hasattr(actor, '_cached_module'):
            try:
                actor._cached_module = import_module(actor.npc.codepath)
            except ImportError:
                log.error("Unable to find module %r", actor.npc.codepath)
                actor._cached_module = None
        if actor._cached_module:
            _run_cb(actor._cached_module, action, kwargs)

def action(action, **kwargs):
    _run_cb(actions, action, kwargs)
    _run_cb(actions, 'got_'+action, kwargs)

    if 'actor' in kwargs:
        _run_fun(kwargs['actor'], action, kwargs)
    if 'target' in kwargs:
        _run_fun(kwargs['target'], 'got_'+action, kwargs)

