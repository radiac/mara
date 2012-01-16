"""
Command registry
"""

# Store global commands in a dict
commands = {}

# Command decorator
def command(name):
    def closure(fn):
        commands[name] = fn
        return fn
    return closure
