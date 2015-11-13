from cletus.contrib.users import UserBase
from cletus.contrib.users.password import PasswordMixin

from .core import service


class User(PasswordMixin, UserBase):
    service = service

