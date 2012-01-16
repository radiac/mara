"""
Commands for IRC-style
"""

@command('me')
def cmd_emote(e):
    write_all("%s %s" % (e.user.name, e.input))
    e.stop()

@command('who')
def cmd_who(e):
    list_users(e.user)

@command('quit')
def cmd_quit(e):
    write(e.user, 'Goodbye!')
    e.user.close()
