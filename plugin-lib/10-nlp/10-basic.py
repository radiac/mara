"""
Very basic natural language processing
This is really stupid, but should suffice for most common requirements
Designed to be replaced by NodeBox's Linguistics for reliable processing
"""

def English_verb_present(word, person=1, negate=False):
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
