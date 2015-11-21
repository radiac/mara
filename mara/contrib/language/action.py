"""
English natural language processing
"""
import re

from .dictionary import *
from . import pronouns


class BaseToken(object):
    def __init__(self, value):
        self.value = value

class VerbToken(BaseToken): pass
class UserToken(BaseToken): pass
class WordToken(BaseToken): pass
class OtherToken(BaseToken): pass


class DirectedAction(object):
    """
    Class to process a directed action string so we can change the person of a
    present-tense verb, and identify and target named users.
    
    Arguments:
        raw     The raw action string to process
        users   A dict of lowercase usernames to user objects.
                A user object can be anything, but it must have a
                .name attribute with the capitalised username in it.
                To enable gender-aware pronouns, make sure the user objects
                also have a .gender attribute, set to one of MALE, FEMALE or
                OTHER from mara.contrib.language.pronouns.
    """
    def __init__(self, raw, users):
        self.raw = raw
        self.known_users = users
        
        self.tokens = []
        self.users = []
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
                if word in VERBS:
                    token = VerbToken(word)
                else:
                    user = self.known_users.get(word.lower())
                    if user:
                        # Check if we need to add a preposition
                        if (
                            # Last word was a verb
                            last_word_token
                            and isinstance(last_word_token, VerbToken)
                            # Last word should have had a preposition here
                            and last_word_token.value in SOCIAL_PREPOSITIONS
                            # Last word was first, just forgot preposition
                            and not last_word_token.last_word_token
                        ):
                            # Add it back
                            self.tokens.append(
                                OtherToken(SOCIAL_PREPOSITIONS[token.value] + ' ')
                            )
                        
                        # Add the user
                        token = UserToken(user)
                        self.users.append(user)
                    else:
                        # Unknown/irrelevant word
                        token = WordToken(word)
                
                token.last_word_token = last_word_token
                last_word_token = token
                self.tokens.append(token)
            
            # Add nonword as OtherToken
            if nonword:
                self.tokens.append(OtherToken(nonword))
        
    def verb_to_second_person(self, token):
        """
        First person present tense verb is the same as second person
        """
        return token.value
        
    def verb_to_third_person(self, token, last_word=None):
        """
        Naive method to change a first person present tense verb to third
        person.
        """
        word = token.value
        
        # Catch conjucations that use first person present conjugations;
        # pretty crude, but should cover most situations
        if last_word in [
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
    
    def second_person(self, user):
        """
        Render the first person string in second person for the specified user
        """
        words = []
        last_word = None
        last_user = {}
        for token in self.tokens:
            # Verbs and other tokens are added straight
            word = token.value
            if isinstance(token, (VerbToken, OtherToken)):
                words.append(word)
                continue
            
            # Verbs are fine
            # Change username to "yourself"
            if isinstance(token, UserToken):
                # Store user by gender
                last_user[
                    getattr(token.value, 'gender', pronouns.OTHER)
                ] = token.value
                
                if token.value == user:
                    word = pronouns.second.self
                else:
                    word = token.value.name
            
            # Change first person pronouns (me) to second person (you)
            elif isinstance(token, WordToken):
                token_value = token.value.lower()
                if token_value.upper() == pronouns.first.subject: # I to you
                    word = pronouns.second.subject
                elif token_value == pronouns.first.object: # me to you
                    word = pronouns.second.object
                elif token_value == pronouns.first.possessive: # my to your
                    word = pronouns.second.possessive
                elif token_value == pronouns.first.self: # myself to yourself
                    word = pronouns.second.self
                
                # Convert third person pronoun to second person if it refers to
                # the user
                elif token_value in pronouns.THIRD_LOOKUP:
                    prn_group, prn_gender = pronouns.THIRD_LOOKUP[token_value]
                    if prn_gender in last_user and last_user[prn_gender] == user:
                        word = prn_group[pronouns.SECOND]
                
                # Change conjugation of to be
                # <user> is -> you is -> you are
                elif (last_word == 'you' and token_value in ['is', 'am']):
                    word = 'are'
                # <source user> am -> he|she am -> he|she is
                elif (last_word in ['he', 'she'] and token_value == 'am'):
                    word = 'is'
                # <source user> am -> they am -> they are
                elif (last_word == 'they' and token_value == 'am'):
                    word = 'are'
            
            words.append(word)
            last_word = word
        return ''.join(words)
        
    def third_person(self, target=None, source=None):
        """
        Render the string in third person, targetted at the optional specified
        target, from the optional specified source
        """
        words = []
        source_gender = pronouns.Pronoun(
            getattr(source, 'gender', pronouns.OTHER)
        )
        last_word = None
        last_user = {}
        for token in self.tokens:
            # Other tokens are added straight
            word = token.value
            if isinstance(token, OtherToken):
                words.append(word)
                continue
            
            # Change verb tense
            if isinstance(token, VerbToken):
                word = self.verb_to_third_person(token, last_word)
            
            # Change username
            elif isinstance(token, UserToken):
                # Store user by gender
                last_user[
                    getattr(token.value, 'gender', pronouns.OTHER)
                ] = token.value
                
                # Source referring to self
                if source and token.value == source:
                    word = source_gender.self
                
                # Source referring to target, change to second person
                elif token.value == target:
                    word = pronouns.second.object
                
                # Source referring to someone else, keep their name
                else:
                    word = token.value.name
            
            elif isinstance(token, WordToken):
                token_value = token.value.lower()
                # Change first person pronouns to third person using source gender
                if token_value.upper() == pronouns.first.subject: # I to he/they
                    word = source_gender.subject
                elif token_value == pronouns.first.object: # me to him/they
                    word = source_gender.object
                elif token_value == pronouns.first.possessive: # my to his/their
                    word = source_gender.possessive
                elif token_value == pronouns.first.self: # myself to himself/themselves
                    word = source_gender.self
                
                # Convert third person pronoun to second person if it refers to
                # the target user
                elif token_value in pronouns.THIRD_LOOKUP:
                    prn_group, prn_gender = pronouns.THIRD_LOOKUP[token_value]
                    if prn_gender in last_user and last_user[prn_gender] == target:
                        word = prn_group[pronouns.SECOND]
                
                # Change conjugation of to be
                # <target user> is -> you is -> you are
                elif (last_word == 'you' and token_value in ['is', 'am']):
                    word = 'are'
                # <source user> am -> he|she am -> he|she is
                elif (last_word in ['he', 'she'] and token_value == 'am'):
                    word = 'is'
                # <source user> am -> they am -> they are
                elif (last_word == 'they' and token_value == 'am'):
                    word = 'are'
                
            # Have the word
            words.append(word)
            last_word = word
        return ''.join(words)

