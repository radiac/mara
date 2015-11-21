"""
Password mixin for BaseUser

Requires bcrypt module: pip install bcrypt
"""
import hashlib

try:
    import bcrypt
except ImportError as e:
    raise ImportError('%s - it is required for PasswordMixin' % e)

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



def prompt_new_password(client):
    """
    Prompt the specified client for a password
    """
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
    
    yield password
