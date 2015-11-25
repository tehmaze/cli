import pwd

from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit.keys import Keys
from pygments.token import Token

from cli.section import Section, command
from cli.style import get_style


class Toolbar:
    def __init__(self, section):
        self.section = section

    def get_tokens(self, cli):
        root = self.section.get_root()
        tokens = [(Token.Toolbar, ' CLI Demo ')]

        if root.theme == 'fruity':
            tokens.append((Token.Toolbar.Completions, ' [F1] Light '))
        else:
            tokens.append((Token.Toolbar.Completions, ' [F1] Dark '))

        return tokens


def keys_factory(section):
    root = section.get_root()
    manager = KeyBindingManager.for_prompt()

    @manager.registry.add_binding(Keys.F1)
    def _(event):
        if root.theme == 'fruity':
            root.theme = 'native'
        else:
            root.theme = 'fruity'
        root._style = get_style(root.theme)

    return manager


class User(Section):
    def __init__(self, parent, username):
        super(User, self).__init__(parent)
        self.name = username
        self.entry = pwd.getpwnam(self.name)

    @command()
    def id(self):
        print('uid={pwd.pw_uid}({pwd.pw_name}), gid={pwd.pw_gid}'.format(
            pwd=self.entry))

    @command()
    def gecos(self):
        print('gecos: {}'.format(self.entry.pw_gecos))

    @command()
    def shell(self):
        print('shell: {}'.format(self.entry.pw_shell))


class UserTree(Section):
    name = 'user'

    def __getitem__(self, key):
        try:
            super(UserTree, self).__getitem__(key)
        except KeyError:
            # `pwd.getpwnam()` raises `KeyError` if not found
            return User(self, pwd.getpwnam(key).pw_name)

    def complete_command(self, query):
        for user in pwd.getpwall():
            if user.pw_name.startswith(query):
                yield user.pw_name, user.pw_gecos


class Test(Section):
    name = 'test'
    toolbar_class = Toolbar

    @command()
    def test(self):
        print('it works')


class Root(Section):
    banner = '''Welcome to the demo command line interface.

For online help, enter: help

Available hot keys:

    <tab>   Complete the command
    <C-d>   Exit current section
    <C-r>   Reverse search history
    <F1>    Toggle between light and dark theme

'''
    keys_factory = keys_factory
    theme = 'fruity'
    toolbar_class = Toolbar

    @command()
    def echo(self, *args):
        print(self._term.bold_yellow('echo: {}'.format(' '.join(args))))

    def run(self):
        self.help()
        super(Root, self).run()


if __name__ == '__main__':
    demo = Root()
    demo.add_section(Test())
    demo.add_section(UserTree())
    demo.run()
