"""
Unauthenticated users
"""
    
def user_name_validate(target, name):
    """
    Validate user's name
    """
    if not name.isalnum():
        target.write('Names must consist of only letters and numbers')
        return False
    
    for user in manager.users:
        if user.name == name:
            target.write('That name is already taken')
            return False
    return True

def user_named(user, name):
    """
    The user has responded to the name prompt
    """
    # Store
    user.name = name

    # Announce
    write_all('-- %s has connected --' % user.name)
    
    # Look
    others = find_others(user)
    if len(others) == 1:
        user.write('Also here: %s' % ', '.join([o.name for o in others]))
    else:
        user.write('Nobody else is here.')

   
#
# Listeners
#

@listen('connect')
def connect(e):
    """
    Do something when the user connected
    """
    e.user.write('-- Welcome to Cletus --')
    e.user.prompt('Enter your name: ', user_named, user_name_validate)

@listen('disconnect')
def disconnect(e):
    write_except(e.user, '-- %s has disconnected --' % e.user.name)
