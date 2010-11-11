from cli.history import History
import unittest

class Test(unittest.TestCase):
    history = History()

    def test_1_len(self):
        self.assertEqual(len(self.history), 0)

    def test_2_append(self):
        self.assertEqual(self.history.append('foo'), None)
        self.assertEqual(self.history.append('bar'), None)
        self.assertEqual(self.history.append('biz'), None)

    def test_3_current(self):
        self.assertEqual(self.history.current(), 'biz')

    def test_4_backward(self):
        self.assertEqual(self.history.backward(), 'bar')

    def test_5_forward(self):
        self.assertEqual(self.history.forward(), 'biz')

    def test_6_complete_backward(self):
        self.assertEqual(self.history.complete_backward('b'), 'biz')

    def test_7_complete_forward(self):
        self.assertEqual(self.history.complete_forward('b'), 'bar')

if __name__ == '__main__':
    unittest.main()

