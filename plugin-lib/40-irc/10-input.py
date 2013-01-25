"""
Input handlers for IRC-style commands and command-less chat
"""

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
    commands[cmd].call(e)

@listen('input')
def input_say(e):
    if e.input:
        write_all("%s: %s" % (e.user.name, e.input))
