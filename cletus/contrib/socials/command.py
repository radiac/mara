"""
Social command management
"""

from cletus.user import User

STANDARD = [
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


def English_verb_present(word, person=1, negate=False):
    """
    Very basic natural language processing, to change the present tense of a
    verb between first and third person.
    
    This is a really naieve implementation, but should suffice for most common
    requirements. Same interface as NodeBox's Linguistics, so should be easy
    to swap for something better.
    """
    if negate:
        if person == 1:
            word = 'do not ' + word
        elif person == 3:
            word = 'does not ' + word
        
    if person == 1:
        return word
        
    elif person == 3:
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


def social(commands, name, *preps):
    """
    Build and register a social command, with optional prepositions
    """
    def closure(event):
        extra = ''
        target = e.args.target
        if target:
            if preps:
                extra = '%s %s' % (e.args.prep or preps[0], target.name)
            else:
                extra = target.name
        
        verb_third = English_verb_present(name, person=3)
        
        if target:
            write(e.user, "You %s %s" % (name, extra))
            write_except(e.user, "%s %s %s" % (e.user.name, verb_third, extra))
        else:
            write(e.user, "You %s" % name)
            write_except(e.user, "%s %s" % (e.user.name, verb_third))
    
    # Build argument list
    args = []
    if preps:
        regex = '|'.join(preps)
        args.append(Arg(
            name = 'prep',
            match = preps[0] if len(preps) == 1 else '(?:' + regex + ')',
            syntax = regex,
            optional = True
        ))
    # ++ Add support for multiple users
    # ++ Add support for User or str
    args.append(Arg('target', User, optional=True))
    
    # Register
    commands.register(name, args=args, group='social')(command)

