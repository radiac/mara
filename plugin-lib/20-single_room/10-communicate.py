"""
Single room management
"""

#
# Maintain a list of users who have logged in
#

# User list must persist across plugin reloads
room_session = manager.session('room')
# ++ Improve this with Session object instead of dict
if not room_session.has_key('users'):
    room_session['users'] = []
users = room_session['users']
if not room_session.has_key('last_list'):
    room_session['last_list'] = [('-- Restart --', manager.time)]
last_list = room_session['last_list']
if not room_session.has_key('messages'):
    room_session['messages'] = []


@listen('login')
def load_user(e):
    if e.user not in users:
        users.append(e.user)

@listen('disconnect')
def unload_user(e):
    if e.user in users:
        # Manage last
        last_list.insert(0, (e.user.name, manager.time))
        if len(last_list) > 10:
            last_list.pop()
        
        # Remove user
        users.remove(e.user)
    

#
# Functions for finding and communicating with users in the room
#

@public
def find_user(name):
    """
    Find a User object from a name
    """
    if not name:
        return None
    
    for user in users:
        if user.name == name:
            return user
    return None

@public
def find_others(target):
    """
    Get a list of users who are visible to the specified user
    Excludes the specified user
    """
    return [user for user in users if user != target]
    
@public
def write(user, *lines):
    """
    Write something to a user
    """
    user.write(*lines)
    
@public
def write_all(*lines):
    """
    Write something to everyone who has logged on
    """
    for user in users:
        user.write(*lines)
    
@public
def write_except(target, *lines):
    """
    Write something to everyone except the specified user
    """
    for user in users:
        if user == target:
            continue
        user.write(*lines)

@public
def list_users(user):
    """
    Tell the specified user who else is here
    """
    others = find_others(user)
    if len(others) >= 1:
        write(user, 'Also here: %s' % ', '.join([o.name for o in others]))
    else:
        write(user, 'Nobody else is here.')

#
# Commands
#
@command
def last(e):
    lines = [util.HR('Latest departures')]
    for name, when in last_list:
        lines.append('%s\t%s' % (
            name, util.pretty_age(now=manager.time, then=when)
        ))
    lines.append(util.HR())
    
    write(e.user, *lines)

@listen('login')
def msg_list(e):
    if not room_session['messages']:
        write(e.user, '-- No messages --')
        return
    lines = [util.HR('Messages')]
    for name, time, message in room_session['messages']:
        lines.append('%s: %s (%s)' % (
            name, message, util.pretty_age(now=manager.time, then=time)
        ))
    lines.append(util.HR())
    
    write(e.user, *lines)

@command('msg', args=[Arg('cmd', '\w+', syntax='(add|show|clear)'), Arg('message', str, optional=True)])
def msg(e):
    if e.args.cmd == 'add':
        if not e.args.message:
            write(e.user, 'You must provide a message')
            return
        room_session['messages'].append((e.user.name, manager.time, e.args.message))
        write(e.user, 'Your message has been added')
        
    elif e.args.cmd == 'show':
        msg_list(e)
        
    elif e.args.cmd == 'clear':
        room_session['messages'] = []
        write(e.user, 'Messages have been cleared')
        
    else:
        write(e.user, 'Valid commands: add, show, clear')
