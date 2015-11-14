from cletus.contrib.users import BaseUser
from cletus.contrib.users.password import PasswordMixin

from .core import service


class User(PasswordMixin, BaseUser):
    service = service

