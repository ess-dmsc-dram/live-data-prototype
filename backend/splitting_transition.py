from checkpoint import CompositeCheckpoint
from mantid_workspace_checkpoint import MantidWorkspaceCheckpoint
from transition import Transition


class SplittingTransition(Transition):
    def __init__(self, parent):
        self._split_count = 1
        super(SplittingTransition, self).__init__(parents=[parent])

    def next(self):
        self._split_count += 1
        self._checkpoint.add_checkpoint(MantidWorkspaceCheckpoint())

    def _do_transition(self, data):
        tmp = [None]*len(self._checkpoint)
        tmp[-1] = data[0].data
        return tmp

    def _create_checkpoint(self):
        return CompositeCheckpoint(MantidWorkspaceCheckpoint, self._split_count)
