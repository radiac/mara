"""
Single room management
"""

#
# Maintain a list of users who have logged in
#

# User list must persist across plugin reloads
room_session = manager.session('room')
if not room_session.has_key('users'):
    room_session['users'] = []
users = room_session['users']

@listen('login')
def load_user(e):
    if e.user not in users:
        users.append(e.user)

@listen('disconnect')
def unload_user(e):
    if e.user in users:
        users.remove(e.user)
    

#
# Commands for finding and communicating with users in the room
#

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

def find_others(target):
    """
    Get a list of users who are visible to the specified user
    Excludes the specified user
    """
    return [user for user in users if user != target]
    
def write(user, *lines):
    """
    Write something to a user
    """
    user.write(*lines)
    
def write_all(*lines):
    """
    Write something to everyone who has logged on
    """
    for user in users:
        user.write(*lines)
    
def write_except(target, *lines):
    """
    Write something to everyone except the specified user
    """
    for user in users:
        if user == target:
            continue
        user.write(*lines)

def list_users(user):
    """
    Tell the specified user who else is here
    """
    others = find_others(user)
    if len(others) >= 1:
        write(user, 'Also here: %s' % ', '.join([o.name for o in others]))
    else:
        write(user, 'Nobody else is here.')
