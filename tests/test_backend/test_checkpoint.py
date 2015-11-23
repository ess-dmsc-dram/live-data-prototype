import unittest

from backend.checkpoint import DataCheckpoint
from backend.checkpoint import CompositeCheckpoint


class TestDataCheckpoint(unittest.TestCase):
    def setUp(self):
        self._checkpoint = DataCheckpoint()

    def test_operator_bool_false_on_init(self):
        self.assertFalse(self._checkpoint)

    def test_operator_bool_true_with_data(self):
        self._checkpoint.replace('abc')
        self.assertTrue(self._checkpoint)

    def test_replace(self):
        self._checkpoint.replace('abc')
        self.assertEqual(self._checkpoint.data, 'abc')
        self._checkpoint.replace('def')
        self.assertEqual(self._checkpoint.data, 'def')

    def test_append(self):
        self._checkpoint.append('abc')
        self.assertEqual(self._checkpoint.data, 'abc')
        self._checkpoint.append('def')
        self.assertEqual(self._checkpoint.data, 'abcdef')

    def test_clear(self):
        self._checkpoint.append('abc')
        self.assertEqual(self._checkpoint.data, 'abc')
        self._checkpoint.clear()
        self.assertEqual(self._checkpoint.data, None)
