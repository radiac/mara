"""
Talker-style communication and commands
"""

#
# Replace command handler
#

events.unlisten('input', input_command)
events.unlisten('input', input_say)

@listen('input')
def input_command(e):
    e.stop()

    if e.input.startswith("'"):
        cmd = 'say'
        input = e.input[1:]
    elif e.input.startswith(';'):
        cmd = 'emote'
        input = e.input[1:]
    elif ' ' in e.input:
        (cmd, input) = e.input.split(' ', 1)
    else:
        cmd = e.input
        input = ''
    
    # Find and run command
    if not commands.has_key(cmd):
        write(e.user, 'That command was not recognised')
        return
    
    e.input = input
    commands[cmd](e)

@command('say')
def cmd_say(e):
    write(e.user, "You say: %s" % e.input)
    write_except(e.user, "%s says: %s" % (e.user.name, e.input))

# Move /me to emote
commands['emote'] = commands['me']
del commands['me']