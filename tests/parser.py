from cli.parser import parse
import unittest

class Test(unittest.TestCase):
    tests = (
        ('test', (
            ['TokenWord',     'test'],
        )),

        ('test | wc -l', (
            ['TokenWord',     'test'],
            ['TokenPipe',     '|'],
            ['TokenWord',     'wc'],
            ['TokenWord',     '-l'],
        )),

        ('this "is a" \'<\' |test \'with "pipes\' > redirect', (
            ['TokenWord',     'this'],
            ['TokenWord',     'is a'],
            ['TokenRedirect', '<'],
            ['TokenPipe',     '|'],
            ['TokenWord',     'test'],
            ['TokenWord',     'with "pipes'],
            ['TokenRedirect', '>'],
            ['TokenWord',     'redirect'],
        )),
    )

    def test_1_word(self):
        for token in parse('test'):
            self.assertEqual(str(token.__class__.__name__), 'TokenWord')
            self.assertEqual(str(token), 'test')

    def test_2_pipe(self):
        for token in parse('|'):
            self.assertEqual(str(token.__class__.__name__), 'TokenPipe')

    def test_3_lines(self):
        for line, tokens in self.tests:
            tokens = iter(tokens)
            for token in parse(line):
                name, word = tokens.next()
                self.assertEqual(token.__class__.__name__, name)
                self.assertEqual(str(token), word)

if __name__ == '__main__':
    unittest.main()

