"""
Unauthenticated users for IRC-style chat
"""

def user_name_validate(target, name):
    """
    Validate user's name
    """
    if not name.isalnum():
        write(target, 'Names must consist of only letters and numbers')
        return False
    
    for user in manager.users:
        if user.name == name:
            write(target, 'That name is already taken')
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
    
    list_users(user)


#
# Listeners
#

@listen('connect')
def connect(e):
    """
    Do something when the user connected
    """
    print "CONNECT"
    write(e.user, '-- Welcome to Cletus --')
    prompt(e.user, 'Enter your name: ', user_named, user_name_validate)

@listen('disconnect')
def disconnect(e):
    write_except(e.user, '-- %s has disconnected --' % e.user.name)
