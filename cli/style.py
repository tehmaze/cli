"""Syntax and prompt highlighting style."""

from prompt_toolkit.styles import PygmentsStyle, default_style_extensions

from pygments.styles import get_style_by_name
from pygments.styles.fruity import FruityStyle


class Style(FruityStyle):
    """Default highlighting style."""

    background_color = None
    styles = {}
    styles.update(default_style_extensions)
    styles.update(FruityStyle.styles)


def style_factory(section):
    """Default style factory creating styles for a section."""
    return PygmentsStyle(Style)


def get_style(name):
    """Get a Pygments style by name and wrap it to work with prompt_toolkit."""
    style = get_style_by_name(name)

    class OverloadedStyle(style):
        styles = {}
        styles.update(default_style_extensions)
        styles.update(style.styles)

    return PygmentsStyle(OverloadedStyle)
