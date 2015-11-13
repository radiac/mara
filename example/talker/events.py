from cletus import events
from cletus import util

from .core import service
from .users import User


@service.listen(events.Receive)
def command_alias(event):
    """
    De-alias command aliases
    """
    # This will be attached to Receive event before standard CommandHandler
    if event.data.startswith("'"):
        event.data = 'say ' + event.data[1:]
    elif event.data.startswith(';'):
        event.data = 'emote ' + event.data[1:]

@service.listen(events.Connect)
def connect(event):
    """Deal with connection"""
    event.client.write('Welcome to the cletus example talker!')
    while True:
        event.client.write('')
        event.client.write_raw('What is your name? ')
        name = yield
        
        # Get user
        user = User.manager.load(name)
        if not user:
            # New user. Confirm they got it right.
            event.client.write(
                'There is nobody with that name.',
            )
            event.client.write_raw(
                'Do you want to create account? (Enter yes or no) ',
            )
            answer = yield
            if not answer.lower().startswith('y'):
                continue
            
            # Set password
            event.client.write(
                'Please pick a password for your account.',
                'Your password must be at least 6 characters long.',
            )
            
            # Grab echo
            event.client.supress_echo = True
            while True:
                event.client.write_raw('Enter a password: ')
                pass_first = yield
                event.client.write()
                if not pass_first:
                    event.client.write('Your password cannot be blank.')
                    continue
                elif len(pass_first) < 6:
                    event.client.write('Your password must be at least 6 characters long.')
                    continue
                    
                event.client.write_raw('Confirm password: ')
                pass_second = yield
                event.client.write()
                if pass_first != pass_second:
                    event.client.write('Passwords do not match. Try again.')
                else:
                    break
            event.client.supress_echo = False
            
            # Create new user and set password
            user = User(name)
            user.name = name
            user.set_password(pass_first)
            user.save()
            event.client.write('Account created!')
            
        else:
            # Authenticate existing user
            event.client.write('A user with that name already exists.')
            event.client.write_raw('Enter your password, or press enter to pick a new name: ')
            event.client.supress_echo = True
            password = yield
            event.client.supress_echo = False
            event.client.write()
            if not password:
                continue
            elif not user.check_password(password):
                event.client.write('Password incorrect.')
                # Return to welcome prompt
                continue
            
            # Authenticated
            User.manager.add_active(user)
        
        # At this point we have a valid user
        break
        
    # Attach the user to the client
    event.client.user = user
    
    # Set or update the user.client
    connect_msg = 'connected'
    if user.client:
        user.client.user = None
        user.client.write('You have logged in from a different connection.')
        user.client.close()
        connect_msg = 'reconnected'
    user.client = event.client
    
    # Announce
    others = [client.user.name for client in service.get_all(exclude=event.client)]
    if not others:
        others = ['Nobody else']
    event.client.write('Welcome, %s! %s %s here' % (
        user.name, util.pretty_list(others),
        'is' if len(others) == 1 else 'are'
    ))
    service.write_all(
        '%s has %s' % (user.name, connect_msg),
        exclude=event.client,
    )


@service.listen(events.Disconnect)
def disconnect(event):
    """Deal with disconnection"""
    # If the client doesn't have a user, it hasn't logged in
    if not getattr(event.client, 'user', None):
        return
    
    # Disconnect the user
    event.user.disconnected()
    service.write_all('%s has disconnected' % event.user.name)
