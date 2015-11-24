import mantid.simpleapi as mantid

from mantid_workspace_checkpoint import MantidWorkspaceCheckpoint
from mantid_workspace_transition import MantidWorkspaceTransition


class MantidRebinTransition(MantidWorkspaceTransition):
    def __init__(self, parent):
        self.bin_parameters = '0.4,0.1,5'
        super(MantidRebinTransition, self).__init__(parents=[parent])

    def _do_transition(self, data):
        tmp = mantid.Rebin(data[0].data, Params=self.bin_parameters, PreserveEvents=False)
        return tmp
