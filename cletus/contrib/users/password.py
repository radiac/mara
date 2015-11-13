"""
Password mixin for UserBase
"""
try:
    import bcrypt
    import hashlib
except ImportError:
    raise ImportError('%s - it is required for PasswordMixin')

from ... import storage

class PasswordMixin(storage.Store):
    """
    Store password using salted bcrypt
    
    Requires bcrypt module: pip install bcrypt
    
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

