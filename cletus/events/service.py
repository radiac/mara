"""
Service events
"""
from .base import Event

__all__ = [
    'PreStart', 'PostStart', 'PreStop', 'PostStop',
]

class PreStart(Event):  "Service starting"
class PostStart(Event): "Service started"
class PreStop(Event):   "Service stopping"
class PostStop(Event):  "Service stopped"
