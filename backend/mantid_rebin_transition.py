import mantid.simpleapi as mantid

from mantid_workspace_checkpoint import MantidWorkspaceCheckpoint
from mantid_workspace_transition import MantidWorkspaceTransition


class MantidRebinTransition(MantidWorkspaceTransition):
    def __init__(self, parent):
        self._bin_parameters = '0.4,0.1,5'
        super(MantidRebinTransition, self).__init__(parents=[parent])

    def set_bin_parameters(self, bin_parameters):
        self._bin_parameters = str(bin_parameters)
        self.trigger_rerun()

    def _do_transition(self, data):
        tmp = mantid.Rebin(data[0].data, Params=self._bin_parameters, PreserveEvents=False)
        return tmp
