"""
Service events
"""
from __future__ import annotations

from .base import Event


__all__ = [
    "App",
    "PreStart",
    "PostStart",
    "PreStop",
    "PostStop",
    "PreRestart",
    "PostRestart",
]


class App(Event):
    "Service event"


class PreStart(App):
    "Service starting"


class PostStart(App):
    "Service started"


class PreStop(App):
    "Service stopping"


class PostStop(App):
    "Service stopped"


class PreRestart(App):
    "Service restarting"


class PostRestart(App):
    "Service restarted"
