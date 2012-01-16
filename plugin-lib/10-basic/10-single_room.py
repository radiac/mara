"""
Single room management
"""

def find_others(target):
    """
    Get a list of users who are visible to the specified user
    Excludes the specified user
    """
    return [user for user in manager.users if user.name and user != target]
    
def write(user, *lines):
    """
    Write something to a user
    """
    user.write(*lines)
    
def write_all(*lines):
    """
    Write something to everyone who has logged on
    """
    for user in manager.users:
        if user.name:
            user.write(*lines)
    
def write_except(target, *lines):
    """
    Write something to everyone except the specified user
    """
    for user in manager.users:
        if user == target or not user.name:
            continue
        user.write(*lines)

def list_users(user):
    """
    Tell the specified user who else is here
    """
    others = find_others(user)
    if len(others) == 1:
        write(user, 'Also here: %s' % ', '.join([o.name for o in others]))
    else:
        write(user, 'Nobody else is here.')
