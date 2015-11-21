"""
Social command management

Expects user_store to be a contrib.users.BaseUser subclass; user objects should
have .name and .client attributes, and an optional .gender attribute for
correct use of pronouns.
"""
from ..language import DirectedAction, SOCIAL_VERBS


__all__ = ['gen_social_cmds']

def gen_social_cmd(service, commands, user_store, verb, parser=DirectedAction):
    """
    Build and register a social command for the specified verb, using the
    specified directed action parser (defaults to DirectedAction)
    """
    def command(event, action):
        if not action:
            action = ''
        action = verb + ' ' + action
        
        users = user_store.manager.active()
        
        parsed = parser(action, users)
        
        # Tell the originating user
        event.client.write(
            'You ' + parsed.second_person(event.user)
        )
        
        # Tell the other targetted users
        for user in set(parsed.users):
            if user == event.user:
                continue
            user.write(
                event.user.name + ' ' + parsed.third_person(user, event.user)
            )
        
        # Tell remaining users
        others = [
            user.client for user in 
            set(users.values()).difference(set([event.user] + parsed.users))
        ]
        if others:
            service.write(
                others,
                event.user.name + ' ' + parsed.third_person(source=event.user),
            )
        
    commands.register(verb, command, args=r'^(.*)$', group='social')
        
def gen_social_cmds(
    service, commands, user_store, verbs=SOCIAL_VERBS, parser=DirectedAction,
):
    """
    Build and register social commands for the specified verbs (must be first
    person, defaults to SOCIALS), using the specified directed action parser
    (defaults to DirectedAction)
    """
    for verb in verbs:
        gen_social_cmd(service, commands, user_store, verb)
