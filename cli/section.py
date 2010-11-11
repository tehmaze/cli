from functools import wraps
import textwrap
import sys
import re

RE_SPACING = re.compile(r'\s+')

def command(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        return func(*args, **kwargs)

    decorated.is_method = True
    return decorated


class Section(object):
    name = None

    def __init__(self, parent=None, aliases=None):
        self.parent = parent
        self.aliases = aliases or {}
        self.children = {}
        if not hasattr(self, 'interface'):
            self.interface = self.root.interface

    def __contains__(self, func):
        try:
            return self[func].is_method
        except AttributeError:
            return False

    def __getitem__(self, func):
        return getattr(self, func)

    @property
    def commands(self):
        for attr in dir(self):
            try:
                if getattr(self, attr).is_method:
                    yield attr
            except AttributeError:
                pass

    @property
    def path(self):
        return self.parent.path + [self.name]

    @property
    def root(self):
        node = self
        while node.parent:
            node = node.parent
        return node

    def addchild(self, section):
        self.children[section.name] = section
        self.children[section.name].parent = self

    def delchild(self, section):
        if section.name in self.children:
            self.children[section.name].parent = None
            del self.children[section.name]

    def getchild(self, name):
        return self.children[name]

    def haschild(self, section):
        if isinstance(section, Section):
            return section.name in self.children
        else:
            return section in self.children

    def lookup(self, line):
        '''
        Lookup a (child) node that will handle the line containing
        a command. This will descend down its children if a matching
        pattern is found.
        '''
        if self.interface.section != self.interface.root:
            part = self.interface.section.path + line.split()
        else:
            part = line.split()

        node = self
        while len(part) > 1:
            name = part.pop(0)
            if node.haschild(name):
                node = node.getchild(name)

        # the node we found in the tree can handle the command
        if part[0] in node:
            return node, part.pop(0), part
        # the rood node can handle the command
        elif part[0] in self.root:
            return self.root, part[0], part
        # no node can handle the command
        else:
            return None, None, part

    def execute(self, line):
        '''
        Execute a command or change to the given section, firstly
        we try to interpret the line as a command; if that fails we
        will descend down the children to see if the given line is
        a section.

        This function returns ``True`` if the line was executed.
        '''
        node, func, args = self.lookup(line)
        if node and func:
            node[func](*args)
            return True
        else:
            part = line.split()
            node = self
            while part:
                name = part.pop(0)
                if node.haschild(name):
                    node = node.getchild(name)
                else:
                    # no matching child section, bail out
                    break

            if len(part) == 0 and node != self:
                self.interface.section = node
                self.interface.sendline('')
                return True

    def complete(self, line, include_root=True):
        part = RE_SPACING.split(line)
        if len(part):
            name = part.pop(0)
        else:
            name = ''

        # if there is no remaining elements after the first word, assume
        # the item we are locating is either a command or a section in
        # this node
        if len(part) == 0:
            cmnds = [c for c in self.commands if c.startswith(name)]
            sects = [s for s in self.children if s.startswith(name)]
            # include root commands, but only if the current node is not the
            # root node
            if include_root and self != self.root:
                cmnds.extend([c for c in self.root.commands if c.startswith(name)])
            # de-duplication
            return list(set(cmnds + sects))
        # otherwise, try to complete the line in the node with a matching
        # name; is all fails, we are not able to complete the request
        else:
            if self.haschild(name):
                # prepend the section name to the completed commands
                return map(lambda item: ' '.join([name, item]),
                    self.getchild(name).complete(' '.join(part),
                        include_root=include_root))
            else:
                return []

    def senddata(self, data):
        return self.interface.send(data)

    def sendline(self, line):
        return self.interface.sendline(line)


class Root(Section):
    def __init__(self, interface):
        self.interface = interface
        Section.__init__(self, None)

    @property
    def path(self):
        return []

    @property
    def root(self):
        return self

    @command
    def help(self, *args, **kwargs):
        '''
        syntax:  help [<command>]
        example: help help

        shows help for the given command
        '''
        if args:
            '''
            args = list(args)
            node = self
            while True:
                if node.haschild(args[0]):
                    node = node.getchild(args.pop(0))
                else:
                    break

            '''

            docs = self._get_doc(*args)
            if docs:
                #hook = node[args[0]]
                #text = '\r\n'.join(textwrap.dedent(hook.__doc__).strip().splitlines())
                text = '\r\n'.join(textwrap.dedent(docs).strip().splitlines())
                if kwargs.get('single', False):
                    self.sendline(text.splitlines()[0])
                else:
                    self.sendline(text)
            else:
                self.sendline('command not found')

        else:
            return self.help('help')

    def _get_doc(self, *args):
        node, func, args = self.lookup(' '.join(args))
        if node and func:
            return node[func].__doc__
        else:
            return ''

    def _get_syntax(self, *args):
        docs = self._get_doc(*args)
        if docs:
            for line in docs.strip().splitlines():
                if line.startswith('syntax:'):
                    return ' '.join(line.split()[2:])
        return ''

    @command
    def history(self, *args):
        '''
        syntax:  history

        shows the command history
        '''
        for i, command in enumerate(self.interface.history):
            if i > 0:
                self.senddata('%d.\t%s\r\n' % (i, command))
        self.senddata(self.interface.prompt)

    @command
    def exit(self, *args):
        '''
        syntax:  exit
        example: exit

        stop the scanner daemon
        '''
        self.senddata('bye\r\n')
        sys.exit(0)

    quit = exit
