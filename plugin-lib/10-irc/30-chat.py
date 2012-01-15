"""
IRC-style chat
"""

# Command decorator
commands = {}
def command(name):
    def closure(fn):
        commands[name] = fn
        return fn
    return closure

@listen('input')
def input_command(e):
    if not e.input.startswith('/'):
        return
    
    e.stop()

    # Split on space
    if ' ' in e.input:
        (cmd, input) = e.input[1:].split(' ', 1)
    else:
        cmd = e.input[1:]
        input = ''
    
    # Find and run command
    if not commands.has_key(cmd):
        write(e.user, 'That command was not recognised')
        return
    
    e.input = input
    commands[cmd](e)

@listen('input')
def input_say(e):
    if e.input:
        write_all("%s: %s" % (e.user.name, e.input))

@command('me')
def cmd_emote(e):
    write_all("%s %s" % (e.user.name, e.input))
    e.stop()

@command('quit')
def cmd_quit(e):
    write(e.user, 'Goodbye!')
    e.user.close()
    