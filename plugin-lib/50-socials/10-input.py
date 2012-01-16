"""
Social command management
"""

def social(cmd, to_others):
    """
    Build and register a social command
    """
    def closure(e):
        write(e.user, "You %s" % cmd)
        write_except(e.user, "%s %s" % (e.user.name, to_others))
    commands[cmd] = Command(cmd, closure)
