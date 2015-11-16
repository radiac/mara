"""
Social command management

Naieve NLP. Should be easy to switch for something more reliable, like
NodeBox's Linguistics.
"""
import re


__all__ = ['gen_social_cmds']

# Social verbs with default prepositions

PREPOSITIONS = {
    'agree': 'with',
    'apologise': 'to',
    'argue': 'with',
    'bark': 'at',
    'beam': 'at',
    'beckon': 'to',
    'beep': 'at',
    'bing': 'at',
    'bingle': 'at',
    'bleep': 'at',
    'blink': 'at',
    'blush': 'at',
    'bow': 'to',
    'bouce': 'around',
    'cackle': 'at',
    'caper': 'around',
    'chuckle': 'at',
    'chortle': 'at',
    'complain': 'to',
    'confess': 'to',
    'cough': 'at',
    'cower': 'behind',
    'crash': 'into',
    'cringe': 'at',
    'croak': 'at',
    'croon': 'at',
    'cuddle': 'up with',
    'curl': 'up with',
    'curse': 'at',
    'curtsey': 'to',
    'dance': 'with',
    'disagree': 'with',
    'discriminate': 'against',
    'dribble': 'on',
    'drool': 'on',
    'eek': 'at',
    'eep': 'at',
    'fart': 'on',
    'fib': 'to',
    'fiddle': 'with',
    'flirt': 'with',
    'flutter': 'around',
    'frolic': 'around',
    'frown': 'at',
    'gape': 'at',
    'gasp': 'at',
    'gawk': 'at',
    'gaze': 'at',
    'gesticulate': 'to',
    'gesture': 'to',
    'giggle': 'at',
    'glare': 'at',
    'gloat': 'at',
    'glower': 'at',
    'grin': 'at',
    'grimace': 'at',
    'grind': 'with',
    'groan': 'at',
    'grovel': 'before',
    'growl': 'at',
    'grumble': 'at',
    'grunt': 'at',
    'guffaw': 'at',
    'gulp': 'at',
    'hiccup': 'at',
    'hiss': 'at',
    'hoot': 'at',
    'hop': 'around',
    'howl': 'at',
    'hrmph': 'at',
    'hmm': 'at',
    'hrm': 'at',
    'hum': 'to',
    'jump': 'on',
    'laugh': 'at',
    'lecture': 'to',
    'leer': 'at',
    'listen': 'to',
    'loom': 'over',
    'meep': 'at',
    'meow': 'at',
    'mime': 'to',
    'moan': 'at',
    'moo': 'at',
    'moose': 'at',
    'mope': 'at',
    'mumble': 'at',
    'mutter': 'at',
    'neigh': 'at',
    'nestle': 'up to',
    'nod': 'at',
    'ook': 'at',
    'ping': 'at',
    'plead': 'to',
    'point': 'at',
    'pose': 'for',
    'pounce': 'on',
    'pout': 'at',
    'prance': 'around',
    'propose': 'to',
    'puke': 'all over',
    'purr': 'at',
    'quack': 'at',
    'rant': 'at',
    'roar': 'at',
    'scamper': 'around',
    'scoff': 'at',
    'scowl': 'at',
    'scream': 'at',
    'screech': 'at',
    'shrug': 'at',
    'shiver': 'at',
    'shriek': 'at',
    'shudder': 'at',
    'sigh': 'at',
    'sing': 'to',
    'sit': 'on',
    'slobber': 'on',
    'smile': 'at',
    'smirk': 'at',
    'snap': 'at',
    'snarl': 'at',
    'sneer': 'at',
    'sneeze': 'at',
    'snicker': 'at',
    'sniff': 'at',
    'sniffle': 'at',
    'snigger': 'at',
    'snore': 'at',
    'snort': 'at',
    'snortle': 'at',
    'snore': 'at',
    'sob': 'at',
    'somersault': 'at',
    'sparkle': 'at',
    'spit': 'at',
    'spy': 'on',
    'squeak': 'at',
    'squeal': 'at',
    'squint': 'at',
    'stare': 'at',
    'sulk': 'at',
    'swagger': 'at',
    'swear': 'at',
    'sympathise': 'with',
    'tango': 'with',
    'tattle': 'on',
    'think': 'about',
    'tremble': 'at',
    'tut': 'at',
    'twinkle': 'at',
    'twirl': 'at',
    'twitch': 'at',
    'vomit': 'at',
    'wail': 'at',
    'wait': 'for',
    'waltz': 'with',
    'wave': 'at',
    'weep': 'at',
    'whimper': 'at',
    'whine': 'at',
    'whinge': 'at',
    'whinny': 'at',
    'whistle': 'to',
    'wibble': 'at',
    'wince': 'at',
    'wiggle': 'at',
    'wink': 'at',
    'wobble': 'at',
    'worry': 'about',
    'yawn': 'at',
    'yodel': 'at',
    'yelp': 'at',
}


# All social verbs
SOCIALS = PREPOSITIONS.keys() + [
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
        last_word_token = None
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
                        # Check if we need to add a preposition
                        if (
                            last_word_token
                            and isinstance(last_word_token, VerbToken)
                            and last_word_token.value in PREPOSITIONS
                        ):
                            self.tokens.append(
                                OtherToken(PREPOSITIONS[token.value] + ' ')
                            )
                        
                        # Add the user
                        token = UserToken(user)
                        self.users.append(user)
                    else:
                        # Unknown/irrelevant word
                        token = OtherToken(word)
                
                token.last_word_token = last_word_token
                last_word_token = token
                self.tokens.append(token)
            
            # Add nonword as OtherToken
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
        
    def verb_to_third_person(self, token):
        """
        Naieve method to change a first person present tense verb to third
        person.
        """
        word = token.value
        last_word_token = getattr(token, 'last_word_token', None)
        
        # Catch conjucations that use first person present conjugations;
        # pretty crude, but should cover most situations
        if last_word_token and last_word_token.value in [
            # Present, not first person
            'you', 'we', 'they',
            # infinitive, future, conditional
            'to', 'will', 'would',
        ]:
            return word
        
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
                words.append(self.verb_to_third_person(token))
            
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
        do_social_cmd(service, parser, event, action)
        
        parsed = parser(action, user_store)
        
        # Tell the originating user
        event.client.write(
            'You ' + parsed.first_person(event.user)
        )
        
        # Tell the other targetted users
        for user in set(parsed.users):
            if user == event.user:
                continue
            user.write(
                event.user.name + ' ' + parsed.third_person(user)
            )
        
        # Tell remaining users
        others = [
            user.client for user in 
            set(user_store.manager.active().values()).difference(
                set([event.user] + parsed.users)
            )
        ]
        if others:
            service.write(others, event.user.name + ' ' + parsed.third_person())
        
    commands.register(verb, command, args=r'^(.*)$', group='social')
        
def gen_social_cmds(service, commands, user_store, verbs=SOCIALS, parser=DirectedAction):
    """
    Build and register social commands for the specified verbs (must be first
    person, defaults to SOCIALS), using the specified directed action parser
    (defaults to DirectedAction)
    """
    for verb in verbs:
        gen_social_cmd(service, commands, user_store, verb)
