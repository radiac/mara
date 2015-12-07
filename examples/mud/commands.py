"""
Mud communication and commands
"""
from .core import service

# Add command handler
from mara.contrib.commands import CommandRegistry
commands = CommandRegistry(service)

# Register standard built-in commands
from mara.contrib.commands import register_cmds as cmds_register_cmds
cmds_register_cmds(commands, admin=True)

# Add room commands - includes room-aware replacements for user commands
from mara.contrib import rooms as contrib_rooms
contrib_rooms.register_cmds(commands, admin=True)
contrib_rooms.register_aliases(commands)

# Add user extensions
from mara.contrib.users.gender import cmd_gender
commands.register('gender', cmd_gender)

from mara.contrib.users.password import ChangePasswordHandler
commands.register('password', ChangePasswordHandler())

from mara.contrib.users.admin import register_cmds as admin_register_cmds
admin_register_cmds(commands)

# Add social commands
from mara.contrib.commands.socials import gen_social_cmds, RoomSocialCommand
gen_social_cmds(commands, command_cls=RoomSocialCommand)
