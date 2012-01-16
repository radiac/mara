"""
Talker-style communication and commands
"""

@command('say')
def cmd_say(e):
    write(e.user, "You say: %s" % e.input)
    write_except(e.user, "%s says: %s" % (e.user.name, e.input))

@command('emote')
def cmd_emote(e):
    write_all("%s %s" % (e.user.name, e.input))
    e.stop()

@command('who')
@command('look')
def cmd_who(e):
    list_users(e.user)

@command('quit')
def cmd_quit(e):
    write(e.user, 'Goodbye!')
    e.user.close()
