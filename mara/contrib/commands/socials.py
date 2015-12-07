"""
Social command management

Expects user_store to be a contrib.users.BaseUser subclass; user objects should
have .name and .client attributes, and an optional .gender attribute for
correct use of pronouns.
"""
from ..language import DirectedAction, SOCIAL_VERBS
from .core import Command

__all__ = ['gen_social_cmds']


class SocialCommand(Command):
    """
    A social command for the specified verb, using a directed action parser
    """
    # Command group to register it in
    group = 'social'
    
    # Directed action parser
    parser = DirectedAction
    
    def __init__(self, name):
        super(SocialCommand, self).__init__(
            name, args=r'^(.*)$', group=self.group,
        )
    
    def get_container(self, event):
        "Get the container for this command"
        return event.service
        
    def fn(self, event, action=None):
        # Find active users
        container = self.get_container(event)
        users = {client.user.key: client.user for client in container.clients}
        
        # Run the directed action parser on the action string
        if not action:
            action = ''
        action = self.name + ' ' + action
        parsed = self.parser(action, users)
        
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
            container.write(
                others,
                event.user.name + ' ' + parsed.third_person(source=event.user),
            )


class RoomSocialCommand(SocialCommand):
    def get_container(self, event):
        return event.user.room


def gen_social_cmds(
    commands, verbs=SOCIAL_VERBS, command_cls=SocialCommand,
    parser=DirectedAction,
):
    """
    Build and register social commands for the specified verbs (must be first
    person, defaults to SOCIALS), using the specified directed action parser
    (defaults to DirectedAction)
    """
    for verb in verbs:
        commands.register(command_cls(verb))
