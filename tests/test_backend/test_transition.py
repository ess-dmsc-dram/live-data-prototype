import unittest
from mock import Mock
from mock import call

from backend.checkpoint import DataCheckpoint
from backend.checkpoint import CompositeCheckpoint
from backend.transition import Transition
from backend.transition import IdentityTransition


class TestTransitionNoParent(unittest.TestCase):
    def setUp(self):
        self._transition = Transition()
        self._transition._do_transition = Mock(return_value = None)

    def test_init(self):
        # No parents, so the rerun triggered by __init__ should to nothing.
        self._transition._do_transition.assert_not_called()

    def test_trigger_update(self):
        update = DataCheckpoint()
        update.append('abc')
        self._transition.trigger_update({'no-parent':update})
        self._transition._do_transition.assert_called_once_with((update,))

    def test_trigger_update_composite(self):
        update = CompositeCheckpoint(DataCheckpoint, 2)
        update.append(['abc','def'])
        self._transition.trigger_update({'no-parent':update})
        calls = [call((update[0],)), call((update[1],))]
        self._transition._do_transition.assert_has_calls(calls)

    def test_trigger_rerun(self):
        # No parents, so rerun should do nothing.
        self._transition.trigger_rerun()
        self._transition._do_transition.assert_not_called()


class ForwardingTransition(Transition):
    def __init__(self):
        super(ForwardingTransition, self).__init__(parents=[])

    def _do_transition(self, data):
        return data[0].data


class TestTransition(unittest.TestCase):
    def setUp(self):
        self._parent = ForwardingTransition()
        self._transition = Transition([self._parent])
        self._transition._do_transition = Mock(return_value = None)

    def test_init(self):
        # Parent has no data, so the rerun triggered by __init__ should to nothing.
        self._transition._do_transition.assert_not_called()

    def test_trigger_update(self):
        update = DataCheckpoint()
        update.append('abc')
        self._parent.trigger_update({'no-parent':update})
        # [0][0] to get first non-keyword argument, [0] to get Checkpoint for first parent
        self.assertEquals(self._transition._do_transition.call_args[0][0][0].data, 'abc')

    def test_trigger_update_composite(self):
        update = CompositeCheckpoint(DataCheckpoint, 2)
        update.append(['abc','def'])
        self._parent.trigger_update({'no-parent':update})
        self._verify_composite_result()

    def test_trigger_rerun(self):
        update = CompositeCheckpoint(DataCheckpoint, 2)
        update.append(['abc','def'])
        self._parent.trigger_update({'no-parent':update})
        self._transition._do_transition.reset_mock()
        # Note: We do not trigger on parent, since that would clear data.
        self._transition.trigger_rerun()
        self._verify_composite_result()

    def test_trigger_rerun_upstream(self):
        update = CompositeCheckpoint(DataCheckpoint, 2)
        update.append(['abc','def'])
        self._parent.trigger_update({'no-parent':update})
        self._transition._do_transition.reset_mock()
        # Parent has no data, rerun will clear output data, and thus also downstream.
        self._parent.trigger_rerun()
        # No data in parent, so this should not be called.
        self._transition._do_transition.assert_not_called()

    def _verify_composite_result(self):
        # Call for first leaf: [0]
        # [0][0] to get first non-keyword argument, [0] to get Checkpoint for first parent
        self.assertEquals(self._transition._do_transition.call_args_list[0][0][0][0].data, 'abc')
        # Call for second leaf: [1]
        self.assertEquals(self._transition._do_transition.call_args_list[1][0][0][0].data, 'def')
