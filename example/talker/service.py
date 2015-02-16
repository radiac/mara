"""
Talker service
"""
import cletus
service = cletus.Service()

from cletus.contrib.commands import CommandRegistry
commands = CommandRegistry(service)

