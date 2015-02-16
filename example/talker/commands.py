"""
Talker-style communication and commands
"""
from .service import service, commands

# Register the ``commands`` command, to list registered commands
from cletus.contrib.commands import cmd_commands, cmd_help, MATCH_STR
commands.register('commands', cmd_commands)
commands.register('help', cmd_help, extra={'cmd_commands': 'commands'})



from cletus.user import User

@commands.register('say', args=MATCH_STR, syntax='[message]')
def say(event, message):
    event.client.write("You say: %s" % message)
    service.write(e.user, "%s says: %s" % (e.user.name, e.args.message))

@command('emote', args=[('action', str)])
def emote(e):
    action = e.args.action
    if not action.startswith("'"):
        action = ' ' + action
    write_all("%s%s" % (e.user.name, action))
    e.stop()

@command('tell', args=[Arg('target', User, many=True), ('message', str)])
def tell(e):
    # ++ A lot of this can probably be made re-usable; add to socials
    # Validate target user
    for target in e.args.target:
        if target == e.user:
            write(e.user, 'Why would you want to tell yourself that?')
            return
        
    # Send
    for target in e.args.target:
        # ++ Need to tell them who else we're talking to
        # ++ Create write_group(list)
        write(target, '%s tells you: %s' % (e.user.name, e.args.message))
    write(e.user, 'You tell %s: %s' % (', '.join([t.name for t in e.args.target]), e.args.message))

@command
def who(e):
    # Find users
    users = find_others(e.user)
    users.append(e.user)
    users.sort(key=lambda user: user.name)
    
    # Build lines of output
    lines = [util.HR('Currently here')]
    for user in users:
        lines.append(
            "%s\t%s" % (user.name, user.client.get_idle_age())
        )
    lines.append(util.HR())
    
    write(e.user, *lines)

@command
def look(e):
    list_users(e.user)
    write_except(e.user, '%s looks around' % e.user.name)

@command
def quit(e):
    write(e.user, util.HR('Goodbye!'))
    e.user.disconnect()
