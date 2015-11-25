"""Command Line Interface lexer for syntax highlighting."""

import re
from operator import add

from pygments import token
from pygments.lexer import RegexLexer, include
from prompt_toolkit.layout.lexers import PygmentsLexer


def _expand_tokens(section, prefix=r'^'):
    from .section import Section

    tokens = {
        'commands': [],
        'sections': [],
    }

    for name, item in section:
        if isinstance(item, Section):
            sub = 'section_{}'.format('_'.join(item._path))
            tokens['sections'].append((
                prefix + re.escape(name) + r'\s*',
                token.Keyword,
                sub,
            ))
            tokens[sub] = add(*_expand_tokens(item, prefix='').values())

        elif callable(item) and hasattr(item, 'command'):
            tokens['commands'].append((
                prefix + re.escape(name) + r'\s*',
                token.Name,
            ))

    return tokens


def lexer_factory(section):
    """Generate a lexer for the given section."""
    class Lexer(RegexLexer):
        flags = re.IGNORECASE | re.DOTALL
        tokens = {
            'root': [
                include('sections'),
                include('commands'),
            ],
        }
        tokens.update(_expand_tokens(section))

    return PygmentsLexer(Lexer)
