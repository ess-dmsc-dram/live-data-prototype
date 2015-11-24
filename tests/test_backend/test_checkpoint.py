import unittest

from backend.checkpoint import Checkpoint
from backend.checkpoint import DataCheckpoint
from backend.checkpoint import CompositeCheckpoint


class TestCheckpoint(unittest.TestCase):
    def setUp(self):
        self._checkpoint = Checkpoint()

    def test_iter(self):
        a = [ i for i in self._checkpoint ]
        self.assertEqual(len(a), 1)

    def test_clear(self):
        self.assertRaises(RuntimeError, self._checkpoint.clear)

    def test_replace(self):
        self.assertRaises(RuntimeError, self._checkpoint.replace, 'abc')

    def test_append(self):
        self.assertRaises(RuntimeError, self._checkpoint.append, 'abc')


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


class TestCompositeCheckpointDefaultInit(unittest.TestCase):
    def setUp(self):
        self._checkpoint = CompositeCheckpoint()

    def test_len(self):
        self.assertEqual(len(self._checkpoint), 0)

    def test_get_item(self):
        cp = DataCheckpoint()
        cp.append('abc')
        self._checkpoint.add_checkpoint(cp)
        self.assertEqual(self._checkpoint[0].data, 'abc')

    def test_set_item(self):
        cp1 = DataCheckpoint()
        cp1.append('abc')
        cp2 = DataCheckpoint()
        cp2.append('def')
        self._checkpoint.add_checkpoint(cp1)
        self.assertEqual(self._checkpoint[0].data, 'abc')
        self._checkpoint[0] = cp2
        self.assertEqual(self._checkpoint[0].data, 'def')

    def test_del_item(self):
        self._checkpoint.add_checkpoint(DataCheckpoint())
        self.assertEqual(len(self._checkpoint), 1)
        del self._checkpoint[0]
        self.assertEqual(len(self._checkpoint), 0)

    def test_del_slice(self):
        self._checkpoint.add_checkpoint(DataCheckpoint())
        self.assertEqual(len(self._checkpoint), 1)
        del self._checkpoint[0:1]
        self.assertEqual(len(self._checkpoint), 0)

    def test_add_checkpoint(self):
        self._checkpoint.add_checkpoint(DataCheckpoint())
        self.assertEqual(len(self._checkpoint), 1)
        self._checkpoint.add_checkpoint(DataCheckpoint())
        self.assertEqual(len(self._checkpoint), 2)

    def test_remove_checkpoint(self):
        self._checkpoint.add_checkpoint(DataCheckpoint())
        self._checkpoint.add_checkpoint(DataCheckpoint())
        self._checkpoint.remove_checkpoint(0)
        self.assertEqual(len(self._checkpoint), 1)
        self._checkpoint.remove_checkpoint(0)
        self.assertEqual(len(self._checkpoint), 0)


class TestCompositeCheckpoint(unittest.TestCase):
    def setUp(self):
        self._checkpoint = CompositeCheckpoint()
        cp1 = DataCheckpoint()
        cp1.append('abc')
        cp2 = DataCheckpoint()
        cp2.append('def')
        self._checkpoint.add_checkpoint(cp1)
        self._checkpoint.add_checkpoint(cp2)

    def test_iter(self):
        a = [ i for i in self._checkpoint ]
        self.assertEqual(len(a), 2)
        self.assertEqual(a[0].data, 'abc')
        self.assertEqual(a[1].data, 'def')

    def test_len(self):
        self.assertEqual(len(self._checkpoint), 2)

    def test_get_slice(self):
        self.assertEqual( [ c.data for c in self._checkpoint[0:2] ], ['abc','def'])

    def test_attribute_data(self):
        self.assertEqual( self._checkpoint.data, ['abc','def'])

    def test_clear(self):
        self._checkpoint.clear()
        self.assertEqual(self._checkpoint.data, [None, None])

    def test_replace(self):
        self.assertEqual( self._checkpoint.data, ['abc','def'])
        self._checkpoint.replace(['ABC','DEF'])
        self.assertEqual( self._checkpoint.data, ['ABC','DEF'])

    def test_append(self):
        self.assertEqual( self._checkpoint.data, ['abc','def'])
        self._checkpoint.append(['ABC','DEF'])
        self.assertEqual( self._checkpoint.data, ['abcABC','defDEF'])


class TestCompositeCheckpointInit(unittest.TestCase):
    def test_leaf_count(self):
        cp = CompositeCheckpoint(leaf_count=3)
        self.assertEqual(len(cp), 3)
