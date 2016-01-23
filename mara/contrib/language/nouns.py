"""
Noun operations
"""
from __future__ import unicode_literals

import re


def plural_noun(noun, count=0):
    """
    Naieve method to pluralise a noun
    """
    if count == 1:
        return noun
    
    if noun.endswith(['s', 'x', 'z', 'ch', 'sh']):
        return noun + 'es'
    
    elif re.search('[^aeiou]y$', noun):
        return noun[:-1] + 'ies'
    
    return noun + 's'    
