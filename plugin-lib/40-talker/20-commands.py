"""
Talker-style communication and commands
"""

@command('say', args=[('message', str)])
def cmd_say(e):
    write(e.user, "You say: %s" % e.args.message)
    write_except(e.user, "%s says: %s" % (e.user.name, e.args.message))

@command('emote', args=[('action', str)])
def cmd_emote(e):
    write_all("%s %s" % (e.user.name, e.args.action))
    e.stop()

@command('tell', args=[('target', ARG_USER), ('message', str)])
def cmd_tell(e):
    # Validate target user
    if e.args.target == e.user:
        write(e.user, 'Why would you want to tell yourself that?')
        return
        
    # Send
    write(e.args.target, '%s tells you: %s' % (e.user.name, e.args.message))
    write(e.user, 'You tell %s: %s' % (e.args.target.name, e.args.message))

@command('who')
def cmd_who(e):
    list_users(e.user)

@command('look')
def cmd_look(e):
    list_users(e.user)
    write_except(e.user, '%s looks around' % e.user.name)

@command('quit')
def cmd_quit(e):
    write(e.user, 'Goodbye!')
    e.user.close()
