"""
Social command management
"""

from cletus.user import User

def English_verb_present(word, person=1, negate=False):
    """
    Very basic natural language processing
    This is really stupid, but should suffice for most common requirements
    Designed to be replaced by NodeBox's Linguistics for reliable processing
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

def social(cmd, *preps):
    """
    Build and register a social command, with optional prepositions
    """
    def closure(e):
        extra = ''
        target = e.args.target
        if target:
            if preps:
                extra = '%s %s' % (e.args.prep or preps[0], target.name)
            else:
                extra = target.name
        
        verb_third = English_verb_present(cmd, person=3)
        
        if target:
            write(e.user, "You %s %s" % (cmd, extra))
            write_except(e.user, "%s %s %s" % (e.user.name, verb_third, extra))
        else:
            write(e.user, "You %s" % cmd)
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
    command(cmd, args=args, group='social')(closure)
