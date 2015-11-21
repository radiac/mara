"""
Service events
"""
from .base import Event

__all__ = [
    'Service',
    'PreStart', 'PostStart', 'PreStop', 'PostStop',
    'PreRestart', 'PostRestart',
]

class Service(Event):       "Service event"
class PreStart(Service):    "Service starting"
class PostStart(Service):   "Service started"
class PreStop(Service):     "Service stopping"
class PostStop(Service):    "Service stopped"
class PreRestart(Service):  "Service restarting"
class PostRestart(Service): "Service restarted"
