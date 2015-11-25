"""Command line bottom toolbar."""

from pygments.token import Token


class Toolbar:
    """Default toolbar."""

    def __init__(self, section):
        """Setup a toolbar for the given section."""
        self.section = section

    def get_tokens(self, cli):
        """Get the toolbar tokens."""
        return [
            (Token.Toolbar, ' Command Line Interface '),
        ]
