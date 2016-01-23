"""
Talker-style communication and commands
"""
from __future__ import unicode_literals

from mara.contrib import users as contrib_users
from mara.contrib.commands import CommandRegistry
from mara.contrib.commands import register_cmds as cmds_register_cmds
from mara.contrib.commands.socials import gen_social_cmds
from mara.contrib.users.admin import register_cmds as admin_register_cmds
from mara.contrib.users.gender import cmd_gender
from mara.contrib.users.password import ChangePasswordHandler

from .core import service


# Add command handler
commands = CommandRegistry(service)

# Register standard built-in commands
cmds_register_cmds(commands, admin=True)

# Add user commands
contrib_users.register_cmds(commands)
contrib_users.register_aliases(commands)

# Add user extensions
commands.register('gender', cmd_gender)
commands.register('password', ChangePasswordHandler())
admin_register_cmds(commands)

# Add social commands
gen_social_cmds(commands)
