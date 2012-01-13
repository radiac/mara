"""
Functionality for calls from the command line
"""

from cletus.core import Manager

def run(settings):
    manager = Manager(settings)
    manager.start()
