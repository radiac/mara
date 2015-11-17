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

# Register the ``commands`` command, to list registered commands
from cletus.contrib.commands import (
    cmd_commands, cmd_help, MATCH_STR, RE_LIST,
)
commands.register('commands', cmd_commands)
commands.register('help', cmd_help, context={'cmd_commands': 'commands'})

# Add social commands
gen_social_cmds(service, commands, User)

# Add gender command
from cletus.contrib.users import gender
commands.register('gender', gender.cmd_gender)

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
def tell(event, *args, **kwargs):
    usernames = args
    msg = kwargs['msg']
    users = User.manager.get_active_by_name(usernames)
    
    # Validate target user
    if event.user.name.lower() in users:
        event.client.write('Why would you want to tell yourself that?')
        return
        
    # Send
    user_objs = users.values()
    for target in user_objs:
        service.write(
            [user.client for user in user_objs],
            '%s tells you: %s' % (event.user.name, msg),
        )
    event.client.write('You tell %s: %s' % (
        util.pretty_list([u.name for u in user_objs]),
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
