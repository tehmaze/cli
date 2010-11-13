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
        self.assertEqual(str(self.sink.stdout), 'testing\nworld\n')
        self.assertEqual(str(self.sink.stderr), '123\nhello\n')
        self.assertEqual(str(self.sink.output), 'testing\n123\nhello\nworld\n')

    def test_3_call(self):
        self.sink.stdout('call')

if __name__ == '__main__':
    unittest.main()

