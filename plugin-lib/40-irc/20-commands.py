"""
Commands for IRC-style
"""

@command('me', args=[('action', str)])
def emote(e):
    write_all("%s %s" % (e.user.name, e.args.action))
    e.stop()

@command
def who(e):
    list_users(e.user)

@command
def quit(e):
    write(e.user, 'Goodbye!')
    e.user.disconnect()
