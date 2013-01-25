"""
Welcome banner for IRC-style
"""

@listen('login')
def msg_list(e):
    write(e.user, 'Type /commands to see available commands')
