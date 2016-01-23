"""
Add user support to service

Must be imported before any events are bound
"""
from __future__ import unicode_literals

from mara.contrib.users import BaseUser
from mara.contrib.users.password import PasswordMixin
from mara.contrib.users.admin import AdminMixin
from mara.contrib.users.gender import GenderMixin
from mara.contrib.rooms import RoomUserMixin

from .core import service

# Add user to client events
from mara import events
from mara.contrib.users import event_add_user
service.listen(events.Client, event_add_user)

# Create User class


class User(RoomUserMixin, PasswordMixin, AdminMixin, GenderMixin, BaseUser):
    service = service
