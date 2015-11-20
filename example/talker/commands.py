"""
Talker-style communication and commands
"""
from cletus import util
from cletus.contrib.users.password import prompt_new_password

from .core import service
from .users import User

# Add command handler
from cletus.contrib.commands import CommandRegistry, gen_social_cmds
commands = CommandRegistry(service)

#
# Build-in commands
#

# Register admin commands
from cletus.contrib.users.admin import if_admin, cmd_list_admin, cmd_set_admin
commands.register('admin', cmd_list_admin, context={'User': User})
commands.register(
    'set_admin', cmd_set_admin, context={'User': User}, can=if_admin,
)

# Register standard built-in commands
from cletus.contrib.commands import (
    cmd_commands, cmd_help, cmd_restart, MATCH_STR, RE_LIST,
)
commands.register('commands', cmd_commands)
commands.register('help', cmd_help, context={'cmd_commands': 'commands'})
commands.register('restart', cmd_restart, can=if_admin)

# Add social commands
gen_social_cmds(service, commands, User)

# Add user commands
from cletus.contrib.users import cmd_list_users
from cletus.contrib.users.gender import cmd_gender
commands.register('users', cmd_list_users, context={'User': User})
commands.register('gender', cmd_gender)


#
# Custom commands
#

@commands.register('say', args=MATCH_STR, syntax='<message>')
def say(event, message):
    event.client.write("You say: %s" % message)
    service.write_all(
        "%s says: %s" % (event.user.name, message),
        exclude=event.client,
    )

@commands.register('emote', args=MATCH_STR, syntax='<action>')
def emote(event, action):
    if not action.startswith("'"):
        action = ' ' + action
    service.write_all("%s%s" % (event.user.name, action))

@commands.register(
    'tell',
    args=r'^' + RE_LIST + '\s+(?P<msg>.*?)$',
    syntax='<user>[, <user>] <message>',
)
def tell(event, usernames, msg):
    usernames = [a.strip() for a in usernames.split(',')]
    users = User.manager.get_active_by_name(usernames)
    
    # Validate target user
    if event.user.name.lower() in users:
        event.client.write('Why would you want to tell yourself that?')
        return
        
    # Send
    user_objs = users.values()
    for target in user_objs:
        targets = util.pretty_list(['you'] + sorted(
            [user.name for user in user_objs if user != target]
        ))
        service.write(
            target.client, '%s tells %s: %s' % (event.user.name, targets, msg),
        )
    event.client.write('You tell %s: %s' % (
        util.pretty_list(sorted([u.name for u in user_objs])),
        msg,
    ))


@commands.register
def who(event):
    # Find users
    users = User.manager.active().values()
    users.sort(key=lambda user: user.name)
    
    # Build lines of output
    lines = [util.HR('Currently here')]
    for user in users:
        lines.append(
            "%s\t%s" % (user.name, user.client.get_idle_age())
        )
    lines.append(util.HR())
    
    event.client.write(*lines)

@commands.register
def look(event):
    service.write_all(
        '%s looks around' % event.user.name,
        exclude=event.client,
    )
    who(event)

@commands.register
def password(event):
    event.user.write('Please pick a new password for your account.')
    # ++ python 3.3 has yield from
    prompt = prompt_new_password(event.client)
    prompt.send(None)
    password = None
    while True:
        try:
            try:
                raw = yield
            except Exception as e:
                prompt.throw(e)
            else:
                password = prompt.send(raw)
        except StopIteration:
            break
        if password:
            break
    # ++ end python 2.7 support
    
    event.user.set_password(password)
    event.user.save()
    event.user.write('Password changed.')

@commands.register
def quit(event):
    event.user.write(util.HR('Goodbye!'))
    event.user.disconnect()
