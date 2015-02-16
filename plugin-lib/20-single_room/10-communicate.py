"""
Single room management
"""

from cletus.storage import Store, Field

class Room(Store):
    messages = Field([], True)
    last = Field()
    users = Field([])
    
    def log_unload(self, username):
        self.last.insert(0, (username, manager.time))
        if len(self.last) > 10:
            self.last.pop()
        
room = Room('room', manager)


#
# Maintain a list of users who have logged in
#

# User list must persist across plugin reloads
room_session = manager.session('room', RoomSession)
@listen('login')
def load_user(e):
    if e.user not in room_session.users:
        room_session.users.append(e.user)

@listen('disconnect')
def unload_user(e):
    if e.user in room_session.users:
        # Manage last
        room_session.log_unload(e.user.name)
        
        # Remove user
        room_session.users.remove(e.user)
    

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
    
    for user in room_session.users:
        if user.name == name:
            return user
    return None

@public
def find_others(target):
    """
    Get a list of users who are visible to the specified user
    Excludes the specified user
    """
    return [user for user in room_session.users if user != target]
    
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
    for user in room_session.users:
        user.write(*lines)
    
@public
def write_except(target, *lines):
    """
    Write something to everyone except the specified user
    """
    for user in room_session.users:
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
    for name, when in room_session.last:
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
