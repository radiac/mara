from cletus.contrib.users import BaseUser
from cletus.contrib.users.password import PasswordMixin
from cletus.contrib.users.gender import GenderMixin

from .core import service


class User(PasswordMixin, GenderMixin, BaseUser):
    service = service
