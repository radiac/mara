"""
Password mixin for BaseUser

Requires bcrypt module: pip install bcrypt
"""
import hashlib

try:
    import bcrypt
except ImportError as e:
    raise ImportError('%s - it is required for PasswordMixin' % e)

from . import base
from ..commands import define_command
from ... import events
from ... import storage


class PasswordMixin(storage.Store):
    """
    Store password using salted bcrypt
    
    Only defined when bcrypt module is available.
    """
    abstract = True
    password = storage.Field()
    
    def hash_password(self, password, salt):
        # Hash using sha512 first to get around 72 character limit
        password = password.encode('utf-8')
        password = password.replace('\x00', '')
        password = hashlib.sha512(password).digest()
        return bcrypt.hashpw(password, salt.encode('utf-8'))
        
    def set_password(self, password):
        """
        Create new salt and hash password
        
        User should be saved after this operation
        """
        salt = bcrypt.gensalt()
        self.password = self.hash_password(password, salt)
    
    def check_password(self, password):
        return self.password == self.hash_password(password, self.password)



class NewPasswordHandler(events.Handler):
    """
    Event handler to collect a new password from a client
    """
    # Flag to skip the new password method, so it can be bypassed in the
    # ConnectHandler subclass
    skip_new_password = False
    
    def handler_50_new_password(self, event):
        """
        Prompt the specified client for a password
        """
        client = event.client
        
        # Not all subclasses will want us to ask for a new password every time
        if self.skip_new_password:
            return
        
        # Set password
        client.write('Your password must be at least 6 characters long.')
        
        # Grab echo
        client.supress_echo = True
        while True:
            client.write_raw('Enter a password: ')
            password = yield
            client.write()
            if not password:
                client.write('Your password cannot be blank.')
                continue
            elif len(password) < 6:
                client.write('Your password must be at least 6 characters long.')
                continue
                
            client.write_raw('Confirm password: ')
            confirm = yield
            client.write()
            if password != confirm:
                client.write('Passwords do not match. Try again.')
            else:
                break
        client.supress_echo = False
        
        self.password_new(password)
    
    def password_new(self, password):
        "New password has been provided"


class CheckPasswordHandler(events.Handler):
    """
    Event handler to prompt the user to enter their password
    
    Subclasses should define a handler_49 (or earlier) method which sets
    .user to the user instance
    """
    # User to check
    user = None
    
    # Flag to skip the check password method, so it can be bypassed in the
    # ConnectHandler subclass
    skip_check_password = False
    
    # Ask to authenticate
    prompt_enter_password = 'Enter your password: '
    
    # Password incorrect
    msg_password_incorrect = 'Password incorrect.'
    
    def handler_50_check_password(self, event):
        # Not all subclasses will want us to check the password
        if self.skip_check_password:
            return
        
        # Prompt and get password
        event.client.write_raw(self.prompt_enter_password)
        event.client.supress_echo = True
        password = yield
        event.client.supress_echo = False
        event.client.write()
        if not password:
            self.password_empty()
        elif not self.user.check_password(password):
            event.client.write(self.msg_password_incorrect)
            # Password incorrect
            self.password_incorrect()
        
        # Password correct
        self.password_correct()
    
    def password_empty(self):
        "No password provided, abort future handlers"
        self.handlers = []
        
    def password_incorrect(self):
        "Password incorrect, abort future handlers"
        self.handlers = []
    
    def password_correct(self):
        "Password correct, continue running handlers"
    

class ConnectHandler(
    NewPasswordHandler, CheckPasswordHandler, base.ConnectHandler,
):
    """
    Connect event handler to authenticate and welcome an existing user, or
    create an account for a new user
    """
    # Flag to control which handlers are run
    is_new_user = False
    
    # Disable NewPasswordHandler if an existing user
    skip_new_password = property(lambda self: not self.is_new_user)
    
    # disable CheckPasswordHandler if a new user
    skip_check_password = property(lambda self: self.is_new_user)
    
    
    # Name does not exist; about to ask to create an account
    msg_new_user = 'There is nobody with that name.'
    
    # Ask to create an account
    prompt_new_user = 'Do you want to create an account? (Enter yes or no) '
    
    # Warn they're about to have to set a password
    msg_new_user_pass = 'Please pick a password for your account.'
    
    # Once new account created
    msg_new_user_created = 'Account created!'
    
    # If a profile can't be loaded for some reason
    msg_profile_corrupt = (
        'That profile is corrupt. Contact the administrator for details.'
    )
    
    # Name does exist; about to ask to authenticate
    msg_user_exists = 'A user with that name already exists.'
    
    # Ask to authenticate
    prompt_enter_password = 'Enter your password, or press enter to pick a new name: '
    
    
    def handler_20_get_user(self, event):
        """
        Look up the user from base.ConnectHandler.handler_10_get_name
        """
        # Get user and auth, or prompt to create account
        User = self.user_store
        self.user = User.manager.load(self.name)
        if not self.user:
            # New user; set flag to control which handlers get run later
            self.is_new_user = True
            
        else:
            # Not a new user; set flag to control future handlers
            self.is_new_user = False
    
        # On to either handler_30_new_user or handler_30_existing_user
    
    def handler_30_new_user(self, event):
        """
        New username; check they want to create a new account
        """
        # Only for new users
        if not self.is_new_user:
            return
            
        # Confirm they got their name right
        event.client.write(self.msg_new_user)
        event.client.write_raw(self.prompt_new_user)
        answer = yield
        if not answer.lower().startswith('y'):
            # Wrong username, start again
            self.handlers = self.get_handlers()
            return
        
        # Tell user we're going to ask them for a password
        event.client.write(self.msg_new_user_pass)
        
        # After this handler, continue on to:
        #   NewPasswordHandler.handler_50_new_password
        # then:
        #   password_new
        #   handler_60_new_user
        
    def password_new(self, password):
        "New password has been provided"
        self.password = password
    
    def handler_60_new_user(self, event):
        """
        Create a new account using password captured by
        NewPasswordHandler.handler_50_new_password
        """
        # Only for new users
        if not self.is_new_user:
            return
            
        User = self.user_store
        
        # Create new user and set password
        self.user = User(self.name)
        self.user.name = self.name
        self.user.set_password(self.password)
        self.user.save()
        event.client.write(self.msg_new_user_created)
        
    def handler_30_existing_user(self, event):
        """
        Authenticate the existing user
        """
        # Only for existing users
        if self.is_new_user:
            return
        
        User = self.user_store
        
        # Catch corrupted profile, rather than dying in bcrypt
        if not self.user.password:
            event.client.write(self.msg_profile_corrupt)
            User.manager.remove_active(self.user)
            event.client.close()
            return
            
        # Authenticate existing user
        event.client.write(self.msg_user_exists)
        
        # After this handler, continue on to:
        #   CheckPasswordHandler.handler_50_check_password
        # then:
        #   password_correct or password_incorrect
        #   handler_60_existing_user
    
    def password_incorrect(self):
        "Password incorrect, start login again"
        self.handlers = self.get_handlers()
    
    def password_correct(self):
        "Password correct, continue running handlers"
    
    def handler_60_existing_user(self, event):
        """
        Log in user, authenticated by
        CheckPasswordHandler.handler_50_check_password
        """
        # Only for existing users
        if self.is_new_user:
            return
            
        # Authenticated
        User = self.user_store
        User.manager.add_active(self.user)
        
        # Make it available for any future events
        event.user = self.user


@define_command(help="Change your password")
class ChangePasswordHandler(NewPasswordHandler):
    """
    Event handler to change password. Normally used by a command::
    
        commands.register('password', ChangePasswordHandler())
    """
    def handler_10_intro(self, event):
        event.user.write('Please pick a new password for your account.')
    
    def password_new(self, password):
        self.event.user.set_password(password)
        self.event.user.save()
        self.event.user.write('Password changed.')
