from cli.sink import Sink
import unittest

class Test(unittest.TestCase):
    sink = Sink()

    def test_1_write(self):
        self.sink.write('testing\n')
        self.sink.error('123\n')
        self.sink.error('hello\n')
        self.sink.write('world\n')

    def test_2_read(self):
        self.assertEqual(self.sink.stdout, 'testing\nworld\n')
        self.assertEqual(self.sink.stderr, '123\nhello\n')
        self.assertEqual(self.sink.output, 'testing\n123\nhello\nworld\n')

if __name__ == '__main__':
    unittest.main()

