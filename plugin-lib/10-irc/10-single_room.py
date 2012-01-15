"""
Single room management
"""

def find_others(target):
    """
    Get a list of users who are visible to the specified user
    Excludes the specified user
    """
    return [user for user in manager.users if user.name and user != target]
    
def write_all(*lines):
    """
    Write something to everyone who has logged on
    """
    for user in manager.users:
        if user.name:
            user.write(*lines)
    
def write_except(self, target, *lines):
    """
    Write something to everyone except the specified user
    """
    for user in manager.users:
        if user == target or not user.name:
            continue
        user.write(*lines)
