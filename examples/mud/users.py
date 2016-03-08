"""
Add user support to service

Must be imported before any events are bound
"""
from __future__ import unicode_literals

from mara import events
from mara.contrib.items import ItemContainerMixin
from mara.contrib.rooms import RoomUserMixin
from mara.contrib.users import BaseUser, event_add_user
from mara.contrib.users.admin import AdminMixin
from mara.contrib.users.gender import GenderMixin
from mara.contrib.users.password import PasswordMixin

from .core import service

# Add user to client events
service.listen(events.Client, event_add_user)


# Create User class
class User(
    ItemContainerMixin, RoomUserMixin, PasswordMixin, AdminMixin, GenderMixin,
    BaseUser,
):
    service = service
