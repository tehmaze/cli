"""Command Line Interface tab completion functionality."""

from prompt_toolkit import completion
from prompt_toolkit.completion import Completion


class Completer(completion.Completer):
    """CLI tab completer that can complete commands and sections."""

    def __init__(self, section):
        """Completer for a CLI section."""
        super(Completer, self).__init__()
        self.section = section

    def get_completions(self, document, event):
        """Get completion suggestions for the current document buffer."""
        from .section import Section

        text = document.text_before_cursor

        if document.char_before_cursor == ' ':
            # We're completing the next item in the sequence
            part = text.rstrip().split()
            complete = ''
        else:
            # We're completing the last item in the sequence
            part = text.split()
            if part:
                complete = part.pop(-1)
            else:
                complete = ''

        path = []
        section = self.section
        command = None
        arguments = []
        for i, item in enumerate(part):
            try:
                section_or_command = section[item]
                if hasattr(section_or_command, 'command'):
                    command = section_or_command
                    arguments = part[i + 1:] + [complete]
                    break
                elif isinstance(section, Section):
                    section = section_or_command
                    path.append(section.name)
                else:
                    return  # Nothing we can tab complete on

            except KeyError:
                return

        if command is None:
            completions = section.complete_command(complete)
        else:
            completions = section.complete_command_args(command, *arguments)

        for suggestion, meta in sorted(list(completions)):
            command = ' '.join(path + [suggestion])
            yield Completion(command, -len(text), display_meta=meta)
