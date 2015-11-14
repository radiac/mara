"""
Social command management

Naieve NLP. Should be easy to switch for something more reliable, like
NodeBox's Linguistics.
"""
import re

__all__ = ['gen_social_cmds']

# Known verbs
SOCIALS = [
    # Simple socials
    'accuse', 'annoy', 'bite', 'blame', 'bribe', 'caress', 'chase', 'chastise',
    'comfort', 'compliment', 'condemn', 'congratulate', 'defenestrate',
    'distract', 'educate', 'elbow', 'encourage', 'envy', 'embarrass',
    'embrace', 'flash', 'flatter', 'fondle', 'forgive', 'glomp', 'grab',
    'greet', 'grope', 'hassle', 'headbutt', 'highfive', 'hit', 'hug', 'hush',
    'kick', 'kiss', 'lick', 'love', 'lynch', 'massage', 'mesmerise', 'moon',
    'mourn', 'nag', 'nudge', 'obey', 'ogle', 'pat', 'patronise', 'pinch',
    'pity', 'pamper', 'pester', 'pet', 'poke', 'prod', 'praise', 'preen',
    'promise', 'punch', 'punish', 'push', 'ram', 'ravish', 'rub', 'remind',
    'salute', 'satisfy', 'scare', 'scold', 'scratch', 'sedate', 'seduce',
    'sentence', 'serenade', 'shake', 'shoo', 'shove', 'shun', 'shush', 'slap',
    'smack', 'smooch', 'snog', 'soothe', 'spam', 'spank', 'squeeze', 'stalk',
    'strangle', 'stroke', 'sue', 'surprise', 'tackle', 'taunt', 'tease',
    'tempt', 'thank', 'threaten', 'tickle', 'toast', 'tongue', 'touch',
    'trust', 'warn', 'welcome',
    
    # These will often have prepositions (with, at etc)
    'agree', 'apologise', 'argue', 'bark', 'beam', 'beckon', 'beep', 'bing',
    'bingle', 'bleep', 'blink', 'blush', 'bow', 'bounce', 'cackle', 'caper',
    'chuckle', 'chortle', 'complain', 'confess', 'cough', 'cower', 'crash',
    'cringe', 'croak', 'croon', 'cuddle', 'curl', 'curse', 'curtsey', 'dance',
    'disagree', 'discriminate', 'dribble', 'drool', 'eek', 'eep', 'fart',
    'fib', 'fiddle', 'flirt', 'flutter', 'frolic', 'frown', 'gape', 'gasp',
    'gawk', 'gaze', 'gesticulate', 'gesture', 'giggle', 'glare', 'gloat',
    'glower', 'grin', 'grimace', 'grind', 'groan', 'grovel', 'growl',
    'grumble', 'grunt', 'guffaw', 'gulp', 'hiccup', 'hiss', 'hoot', 'hop',
    'howl', 'hrmph', 'hmm', 'hrm', 'hum', 'jump', 'laugh', 'lecture', 'leer',
    'listen', 'loom', 'meep', 'meow', 'mime', 'moan', 'moo', 'moose', 'mope',
    'mumble', 'mutter', 'neigh', 'nestle', 'nod', 'ook', 'ping', 'plead',
    'point', 'pose', 'pounce', 'pout', 'prance', 'propose', 'puke', 'purr',
    'quack', 'rant', 'roar', 'scamper', 'scoff', 'scowl', 'scream', 'screech',
    'shrug', 'shiver', 'shriek', 'shudder', 'sigh', 'sing', 'sit', 'slobber',
    'smile', 'smirk', 'snap', 'snarl', 'sneer', 'sneeze', 'snicker', 'sniff',
    'sniffle', 'snigger', 'snore', 'snort', 'snortle', 'snore', 'sob',
    'somersault', 'sparkle', 'spit', 'spy', 'squeak', 'squeal', 'squint',
    'stare', 'sulk', 'swagger', 'swear', 'sympathise', 'tango', 'tattle',
    'think', 'tremble', 'tut', 'twinkle', 'twirl', 'twitch', 'vomit', 'wail',
    'wait', 'waltz', 'wave', 'weep', 'whimper', 'whine', 'whinge', 'whinny',
    'whistle', 'wibble', 'wince', 'wiggle', 'wink', 'wobble', 'worry', 'yawn',
    'yodel', 'yelp',
    
    # These will often have adjectives
    'applaud', 'boo', 'bleat', 'bleed', 'breakdance', 'breathe', 'burp',
    'cheer', 'chew', 'clap', 'code', 'collapse', 'cry', 'daydream', 'declare',
    'duck', 'explode', 'faint', 'fall', 'feel', 'fidget', 'glow', 'gurgle',
    'hate', 'idle', 'melt', 'nap', 'panic', 'pant', 'ponder', 'protest',
    'prepare', 'quote', 'relax', 'sleep', 'spin', 'squirm', 'stagger',
    'stumble', 'suck', 'sweat', 'volunteer', 'win', 'wobble', 'wonder',
]

class BaseToken(object):
    def __init__(self, value):
        self.value = value

class VerbToken(BaseToken): pass
class UserToken(BaseToken): pass
class OtherToken(BaseToken): pass

class DirectedAction(object):
    """
    Class to process a directed action string so we can change the person of a
    present-tense verb, and identify and target named users.
    
    Designed to work with a contrib.users.BaseUser store in a roomless
    environment, but should be easy to subclass for other behaviours.
    """
    def __init__(self, raw, user_store):
        self.raw = raw
        self.user_store = user_store
        
        self.tokens = []
        self.users = []
        self.find_known_users()
        self.parse()
    
    def parse(self):
        """
        Parse the raw action into self.tokens, and any discovered users into
        self.users
        """
        self.tokens = []
        self.users = []
        raw = self.raw.strip()
        while raw:
            # Pop next word and non-word
            match = re.match(r'(\w*)(\W*)', raw)
            raw = raw[len(match.group(0)):]
            word = match.group(1)
            nonword = match.group(2)
            
            # Parse word
            if word:
                if word in SOCIALS:
                    token = VerbToken(word)
                else:
                    user = self.to_user(word)
                    if user:
                        token = UserToken(user)
                        self.users.append(user)
                    else:
                        # Unknown/irrelevant word
                        token = OtherToken(word)
                        
                self.tokens.append(token)
            if nonword:
                self.tokens.append(OtherToken(nonword))
        
    def find_known_users(self):
        """
        Collect targetable users into self.known_users dict, with lowercase
        names used as keys
        """
        self.known_users = self.user_store.manager.active()
        
    def to_user(self, value):
        """
        Return the user object corresponding to the value (name), or None
        if not found.
        
        It can be anything, but gen_social and gen_socials will expect the
        value to have a .name attribute and a .client attribute for it to write
        to, and for the current user to be in event.user
        """
        return self.known_users.get(value.lower())
        
    def verb_to_third_person(self, word):
        """
        Naieve method to change a first person present tense verb to third
        person.
        """
        # Last 2 chars
        if word[-2:] in ('sh', 'ch'):
            word = word + 'es'
            
        elif word[-2:] == 'ey':
            if not word.endswith('obey'):
                word = word[:-2] = 'ies'
            
        # Last char
        elif word[-1:] == 'y':
            word = word[:-1] + 'ies'
            
        elif word[-1:] in ('s', 'x'):
            word = word + 'es'
        
        else:
            word += 's'
        
        return word
    
    def first_person(self, user):
        """
        Render the string in first person for the specified user
        """
        words = []
        for token in self.tokens:
            # Verbs are fine
            # Change username to "yourself"
            if isinstance(token, UserToken):
                if token.value == user:
                    words.append('yourself')
                else:
                    words.append(token.value.name)
            else:
                words.append(token.value)
        return ''.join(words)
        
    def third_person(self, user=None):
        """
        Render the string in third person for the optional specified user
        """
        words = []
        for token in self.tokens:
            # Change verb tense
            if isinstance(token, VerbToken):
                words.append(self.verb_to_third_person(token.value))
            
            # Change username to "you"
            elif isinstance(token, UserToken):
                if token.value == user:
                    words.append('you')
                else:
                    words.append(token.value.name)
            
            # Change "my" to "their"
            elif isinstance(token, OtherToken) and token.value == 'my':
                # ++ gender
                words.append('their')
            
            else:
                words.append(token.value)
        return ''.join(words)


## ++ refactor
# needs to be a Command subclass
# some verbs need default prepositions

def gen_social_cmd(service, commands, user_store, verb, parser=DirectedAction):
    """
    Build and register a social command for the specified verb, using the
    specified directed action parser (defaults to DirectedAction)
    """
    def command(event, action):
        if not action:
            action = ''
        action = verb + ' ' + action
        
        parsed = parser(action, user_store)
        
        # Tell the originating user
        service.write_all('-- FIRST --')
        event.client.write(
            'You ' + parsed.first_person(event.user)
        )
        
        # Tell the other targetted users
        service.write_all('-- THIRD TARGET --')
        for user in set(parsed.users):
            if user == event.user:
                continue
            event.client.write(
                event.user.name + ' ' + parsed.third_person(user)
            )
        
        # Tell remaining users
        service.write_all('-- OTHERS --')
        others = [
            user.client for user in 
            set(user_store.manager.active().values()).difference(
                set([event.user] + parsed.users)
            )
        ]
        if others:
            service.write(others, event.user.name + ' ' + parsed.third_person())
        
    commands.register(verb, command, args=r'^(.*)$')
        
def gen_social_cmds(service, commands, user_store, verbs=SOCIALS, parser=DirectedAction):
    """
    Build and register social commands for the specified verbs (must be first
    person, defaults to SOCIALS), using the specified directed action parser
    (defaults to DirectedAction)
    """
    for verb in verbs:
        gen_social_cmd(service, commands, user_store, verb)
