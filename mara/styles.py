"""
Client-aware string styling and effects
"""
from __future__ import unicode_literals

__all__ = [
    'String',
    'normal', 'bold', 'faint', 'italic', 'underline', 'negative', 'strike',
    'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white',
    'hr',
]


# ANSI_CSI<style>[;<style>]ANSI_FINAL
ANSI_CSI = '\033['
ANSI_END = 'm'

# Style codes
NORMAL      = '0'
BOLD        = '1'
FAINT       = '2'
ITALIC      = '3'
UNDERLINE   = '4'
NEGATIVE    = '7'
STRIKE      = '9'

# Foreground colours
RED         = '31'
GREEN       = '32'
YELLOW      = '33'
BLUE        = '34'
MAGENTA     = '35'
CYAN        = '36'
WHITE       = '37'


class State(object):
    """
    Hold style state and render the ANSI sequence
    """
    # SGR codes
    codes = None
    
    def __init__(self, *codes):
        self.codes = list(codes)
    
    def append(self, code):
        self.codes.append(code)
    
    def pop(self):
        self.codes.pop()
    
    def render(self):
        """
        Render the ANSI escape sequence
        """
        return ANSI_CSI + ';'.join(
            # Always reset, in case we removed a style
            ['0']
            # Add all SGR codes (don't bother deduping)
            + self.codes
        ) + ANSI_END
    
    def __add__(self, state):
        return self.__class__(*(self.codes + state.codes))


class StatePlain(State):
    """
    Version of State which won't render any ANSI sequences
    """
    def render(self):
        return ''


class String(object):
    """
    A container of a list of strings or String instances, which concatenates
    and modifies them when rendered, based on the Client and State.
    """
    def __init__(self, *content):
        self.content = content
    
    def render(self, client, state):
        # Render content to string
        out = state.render()
        for bit in self.content:
            if isinstance(bit, String):
                bit = bit.render(client, state)
            out += bit
        return out
    
    def __add__(self, other):
        return self.__class__(*(self.content + [other]))


class Style(String):
    # The SGR code
    code = None
    
    def render(self, client, state):
        # Add code and render state
        state.append(self.code)
        
        # Add content
        out = super(Style, self).render(client, state)
        
        # Reset state
        state.pop()
        
        return out


# Styles
class normal(Style):    code = NORMAL
class bold(Style):      code = BOLD
class faint(Style):     code = FAINT
class italic(Style):    code = ITALIC
class underline(Style): code = UNDERLINE
class negative(Style):  code = NEGATIVE
class strike(Style):    code = STRIKE

# Foreground colours
class red(Style):       code = RED
class green(Style):     code = GREEN
class yellow(Style):    code = YELLOW
class blue(Style):      code = BLUE
class magenta(Style):   code = MAGENTA
class cyan(Style):      code = CYAN
class white(Style):     code = WHITE


class hr(String):
    """
    Horizontal rule, with centered content
    """
    def render(self, client, state):
        # Use settings state as default (if set)
        if client.service.settings.hr_state:
            state = client.service.settings.hr_state + state
        
        # Build a pattern the size of the client's terminal
        sequence = client.service.settings.hr_sequence
        len_sequence = len(sequence)
        pattern = (
            # Ceiling division to build it bigger and cut it down
            sequence * ((client.columns // len_sequence) + 1)
        )[:client.columns]
        
        # If no content, skip the rest and return with state
        if not self.content:
            return state.render() + pattern
        
        # Calculate left and right padding using width of content without style
        text_only = super(hr, self).render(client, StatePlain())
        space = (client.columns - (len(text_only) + 2))
        left = space // 2
        right = left
        if space % 2:
            right += 1
        
        # If it's a wide sentence or a narrow term, ensure we've got something
        if left < len_sequence:
            left = len_sequence
        if right < len_sequence:
            right = len_sequence
        
        # Render again but with style, and return with state
        out = super(hr, self).render(client, state)
        return state.render() + pattern[:left] + ' ' + out + ' ' + pattern[-right:]
