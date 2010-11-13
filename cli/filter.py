from cli.section import Section, command
import getopt
import re

class Filter(Section):
    RE_LINE = re.compile(r'(?:\r\n|\n)')

    def __init__(self, interface):
        Section.__init__(self, None, interface=interface)

    @command
    def grep(self, sink, *args):
        '''
        syntax:  grep [<options>] <pattern>
        example: grep test

        options:
            -c  Suppress normal output; instead print a count of matching lines
            -i  Ignore case distinctions
            -v  Invert the sense of matching, to select non-matching lines
        '''
        try:
            opts, argv = getopt.getopt(args, 'civ')
            opts = dict(opts)
        except getopt.GetoptError, error:
            sink.stdout.flush()
            sink.error(''.join(['grep: ', str(error), '\r\n']))
            raise StopIteration

        try:
            if '-i' in opts:
                patt = re.compile(' '.join(argv), re.I)
            else:
                patt = re.compile(' '.join(argv))
        except Exception, error:
            sink.stdout.flush()
            sink.error(''.join(['grep: ', str(error), '\r\n']))
            raise StopIteration

        if '-v' in opts:
            test = lambda line: not patt.match(line)
        else:
            test = lambda line: patt.match(line)

        output = []
        for line in self.RE_LINE.split(str(sink.stdout)):
            if test(line):
                output.append(''.join([line, '\r\n']))

        if '-c' in opts:
            sink.stdout = '%d\r\n' % (len(output),)
        else:
            sink.stdout = ''.join(output)

    @command
    def inc(self, sink, *args):
        return self.grep(sink, re.escape(' '.join(args)))

    @command
    def exc(self, sink, *args):
        return self.grep(sink, '-v', re.escape(' '.join(args)))

    include = inc
    exclude = exc

    @command
    def head(self, sink, *args):
        try:
            opts, argv = getopt.getopt(args, 'n:')
            opts = dict(opts)
        except getopt.GetoptError, error:
            sink.stdout.flush()
            sink.error(''.join(['head: ', str(error), '\r\n']))
            raise StopIteration

        try:
            count = int(opts['n'])
        except ValueError:
            sink.stdout.flush()
            sink.error('head: invalud numeric value')
            raise StopIteration

        lines = self.RE_LINE.split(str(sink.stdout))
        sink.stdout.flush()
        for i, line in enumerate(lines):
            if i < count:
                sink.write(''.join([line, '\r\n']))
            else:
                break

