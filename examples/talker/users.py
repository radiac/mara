"""
Add user support to service

Must be imported before any events are bound
"""

from mara.contrib.users import BaseUser
from mara.contrib.users.password import PasswordMixin
from mara.contrib.users.admin import AdminMixin
from mara.contrib.users.gender import GenderMixin

from .core import service

# Add user to client events
from mara import events
from mara.contrib.users import event_add_user
service.listen(events.Client, event_add_user)

# Create User class
class User(PasswordMixin, AdminMixin, GenderMixin, BaseUser):
    service = service


# Give client class a serialiser for the user attribute
from mara.contrib.users import BaseUserSerialiser

class UserSerialiser(BaseUserSerialiser):
    service = service
    store_name = 'user'
    attr = 'user'
