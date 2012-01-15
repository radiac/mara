"""
IRC-style chat
"""

@listen('input')
def input(e):
    if e.input:
        write_all("%s: %s" % (e.user.name, e.input))

class emote(InputProcessor):
    def parse(self, user, input):
        if not input.startswith('/me '):
            return False
        return input[4:].split(' ')

    def process(self, user, parsed):
        write_all("%s %s" % (user.name, parsed))
