"""Command line sections."""

import inspect
from functools import wraps
import re
import textwrap

from blessed import Terminal
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from pygments.token import Token

from .lock import ThreadLock
from .completer import Completer
from .lexer import lexer_factory
from .style import style_factory
from .toolbar import Toolbar


#: Regular expression to match one or more spaces
RE_SPACES = re.compile(r'\s+')


def get_syntax(func, name=None, argspec=None):
    """Get the function call syntax."""
    spec = [name or func.__name__]

    argspec = argspec or inspect.getargspec(func)
    if argspec.args:
        if argspec.args[0] == 'self':
            argspec.args.pop(0)

        if argspec.defaults is None:
            defaults = 0
        else:
            defaults = len(argspec.defaults)
        required = len(argspec.args)

        for i in range(required - defaults):
            spec.append('<{}>'.format(argspec.args[i]))
        for i in range(required - defaults, required):
            spec.append('[<{}>]'.format(argspec.args[i]))

    return ' '.join(spec)


def command(name=None, aliases=[]):
    """Command function decorator."""
    def _decorate(func):
        argspec = inspect.getargspec(func)

        @wraps(func)
        def _decorator(*args, **kwargs):
            return func(*args, **kwargs)

        # Add helper attributes for the section parser
        _decorator.argspec = argspec
        _decorator.command = name or func.__name__
        _decorator.aliases = aliases
        _decorator.syntax = get_syntax(func, _decorator.command, argspec)

        return _decorator
    return _decorate


class Section:
    """Class representing a section (with commands)."""

    #: Name of (sub) section
    name = None

    #: Banner to display when the section is entered
    banner = None

    completer_class = Completer
    history_class = InMemoryHistory
    keys_factory = None
    lexer_factory = lexer_factory
    style_factory = style_factory
    toolbar_class = Toolbar

    def __init__(self, parent=None):
        """Setup a new section. If this is a child section, pass a `parent`."""
        self._parent = parent
        self._parent_lock = ThreadLock()

        self._sections = {}
        self._commands = {}
        self._running = False

        for attr in dir(self):
            method = getattr(self, attr)
            if not callable(method):
                continue

            command = getattr(method, 'command', False)
            if command:
                aliases = getattr(method, 'aliases', [])
                for item in set([command] + aliases):
                    self.add_command(item, method)

        self._term = Terminal()
        self._completer = self.completer_class(self)
        self._history = self.history_class()
        self._lexer = self.lexer_factory()
        self._style = self.style_factory()
        self._toolbar = self.toolbar_class(self)
        if self.keys_factory:
            self._keys_registry = self.keys_factory().registry
        else:
            self._keys_registry = None

    def __add__(self, *other):
        """Add one or more child sections."""
        for section in other:
            self.add_section(section)
        return self

    def __call__(self, command):
        """Dispatch a command or section jump."""
        part = RE_SPACES.split(command.strip())
        if not part:
            return

        if part[0] == '\x1a':  # SUB or ^Z
            self._running = False
            return

        try:
            item = self[part[0]]
        except KeyError:
            self.command_not_found(part[0], *part[1:])
            return

        if isinstance(item, Section):
            if len(part) > 1:
                # We have more arguments, pass it as command to the section
                # without entering the run loop.
                item(' '.join(part[1:]))
            else:
                # No arguments, continue in the nested section.
                item.run()

        else:
            min_args = len(item.argspec.args)
            max_args = min_args
            if item.argspec.defaults:
                min_args -= len(item.argspec.defaults)

            args = part[1:]
            if len(args) < min_args:
                self._error('missing required arguments {}'.format(
                    ', '.join(item.argspec.args[len(args):])))

            elif len(args) > max_args and not item.argspec.varargs:
                self._error('too many arguments')

            else:
                # Dispatch command
                item(*args)

    def __contains__(self, key):
        """Check if the given key is a valid child section or command."""
        return key in self._sections or key in self._commands

    def __enter__(self):
        """Allow the section to be called as a context manager."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the context manager."""
        return

    def __getitem__(self, key):
        """Get a section or command."""
        try:
            return self._sections[key]
        except KeyError:
            pass
        try:
            return self._commands[key]
        except KeyError:
            pass
        raise KeyError('No such section or command "{}"'.format(key))

    def __iter__(self):
        """Iterate over all sections and commands."""
        for name, section in sorted(self._sections.items()):
            yield name, section
        for name, command in sorted(self._commands.items()):
            if name in self._sections:
                continue  # masked by section with the same name
            yield name, command

    def add_command(self, name, fn):
        """Add a named command callback function."""
        assert name not in self._commands, 'Duplicate "{}"'.format(command)
        assert callable(fn)
        self._commands[name] = fn

    def add_section(self, section, name=None):
        """Add a named child section."""
        name = name or section.name
        assert name, 'Subsections must have a name'
        self._sections[name] = section
        self._sections[name].set_parent(self)

        # Update lexer
        self._lexer = self.lexer_factory()

    def get_root(self):
        """Get the root section."""
        with self._parent_lock:
            if self._parent is None:
                return self
            return self._parent

    def get_parent(self):
        """Get the parent section."""
        with self._parent_lock:
            return self._parent

    def set_parent(self, parent):
        """Set the parent section and update the lexer."""
        with self._parent_lock:
            self._parent = parent

        # Update lexer
        self._lexer = self.lexer_factory()

    def complete_command(self, query):
        """Complete a command or section based on `query`.

        The `query` will contain the text before the cursor.
        """
        def _doc(what, default=None):
            try:
                return what.__doc__.splitlines()[0].strip()
            except AttributeError:
                return default

        for name, section in self._sections.items():
            if name.startswith(query):
                yield name, _doc(section, 'Sub section')
        for name, command in self._commands.items():
            if name.startswith(query):
                yield name, _doc(command)

    def complete_command_args(self, command, *args):
        """Complete the command arguments.

        If there is a `_complete_$command` method on the class, the method is
        called to yield completion suggestions for the supplied arguments.
        """
        method = '_complete_{}_args'.format(command.command)
        completion_hook = getattr(self, method, None)
        if completion_hook is not None:
            yield from completion_hook(*args)

    def _error(self, message):
        """Display an error to the user."""
        print(self._term.bright_red('Error: ' + message))

    @property
    def _path(self):
        """List with all section names up to the root."""
        path = []
        with self._parent_lock:
            if self._parent:
                path.extend(self._parent._path)
        if self.name is not None:
            path.append(self.name)
        return path

    @property
    def _prompt(self):
        """Prompt string."""
        return '{}% '.format(' '.join(self._path))

    def _prompt_tokens(self, cli):
        """Prompt tokens."""
        return [
            (Token.Prompt, ' '.join(self._path)),
            (Token.Prompt.Arg, '% '),
        ]

    def run(self):
        """Parse user input until termination is requested."""
        if self.banner:
            print(self.banner)

        self._running = True
        while self._running:
            try:
                result = prompt(
                    completer=self._completer,
                    get_bottom_toolbar_tokens=self._toolbar.get_tokens,
                    get_prompt_tokens=self._prompt_tokens,
                    history=self._history,
                    lexer=self._lexer,
                    key_bindings_registry=self._keys_registry,
                    mouse_support=True,
                    patch_stdout=True,
                    style=self._style,
                )
            except EOFError:
                self._running = False
            else:
                if result:
                    self(result)

    def command_not_found(self, item, *args):
        """Handle a command not found that has been previously dispatched."""
        self._error('unknown command or section "{}"'.format(item))

    @command()
    def help(self, command=None):
        """Show the available commands, or help for the specified command.

        This command is available in all sections. If the command is omitted, a
        list of available commands and sections is printed to the screen.
        """
        if command is None:
            if self._commands:
                print(self._term.bold_white('available commands:'))
                for item in sorted(self._commands):
                    print('    ' + self._commands[item].syntax)
                print('')
            if self._sections:
                print(self._term.bold_white('available sections:'))
                for item in sorted(self._sections):
                    print('    ' + item)
                print('')

        elif command in self._sections:
            print('Function:\n\n    Go to the "{}" section\n'.format(command))
            print('Syntaxis:\n\n    {}\n'.format(command))

        elif command in self._commands:
            docs = self._commands[command].__doc__

            if docs:
                docs = [line for line in docs.splitlines() if docs or line]
                print('Function:\n\n    {}\n'.format(
                    docs[0].strip(' .\t\n\r')))
                print('Syntaxis:\n\n    {}\n'.format(
                    self._commands[command].syntax))

                if len(docs) > 1:
                    print('description:\n')
                    docs = textwrap.dedent('\n'.join([
                        line for line in docs[1:] if docs or line]))
                    for line in textwrap.wrap(docs, initial_indent=''):
                        print('    {}'.format(line))

            else:
                self._error('{}: undocumented command'.format(command))

        else:
            self._error('unknown command or section "{}"'.format(command))

    def _complete_help_args(self, *args):
        """Complete the help function arguments."""
        # The help funciton takes one argument
        if len(args) != 1:
            return

        for suggestion, meta in self.complete_command(args[0]):
            yield 'help ' + suggestion, meta

    @command(aliases=['quit'])
    def exit(self):
        """Terminate the command line session."""
        self._running = False
