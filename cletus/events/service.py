"""
Service events
"""
from .base import Event

__all__ = [
    'PreStart', 'PostStart', 'PreStop', 'PostStop',
    'PreRestart', 'PostRestart',
]

class PreStart(Event):  "Service starting"
class PostStart(Event): "Service started"
class PreStop(Event):   "Service stopping"
class PostStop(Event):  "Service stopped"
class PreRestart(Event):  "Service restarting"
class PostRestart(Event): "Service restarted"
