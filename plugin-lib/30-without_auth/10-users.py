"""
Unauthenticated users for IRC-style chat
"""

#
# Prompt callbacks
#

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
    # Update user and client
    user.name = name
    user.logged_in = True
    user.client.timeout_time = manager.settings.user_timeout
    
    # Announce and welcome
    write_all('-- %s has connected --' % user.name)
    list_users(user)
    
    # Send login event
    events.call('login', Event(
        user = user
    ))


#
# Listeners
#

@listen('connect')
def connect(e):
    """
    Do something when the user connected
    """
    write(e.user, HR('Welcome to Cletus!'))
    prompt(e.user, 'Enter your name: ', user_named, user_name_validate)
    
@listen('disconnect')
def disconnect(e):
    if not e.user.logged_in:
        return
    write_except(e.user, '-- %s has disconnected --' % e.user.name)
    events.call('logout', Event(
        user = e.user
    ))


#
# Commands
#

@command('name', args=[('name', str)])
def cmd_name(e):
    name = e.args.name
    if not user_name_validate(e.user, name):
        return
    write(e.user, 'Name changed to %s' % name)
    write_except(e.user, '-- %s changed their name to %s --' % (e.user.name, name))
    e.user.name = name
