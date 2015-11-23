import mantid.simpleapi as mantid

from checkpoint import DataCheckpoint


class MantidWorkspaceCheckpoint(DataCheckpoint):
    def __init__(self):
        super(MantidWorkspaceCheckpoint, self).__init__()

    def _set_data(self, data):
        if self._data is not None:
            mantid.DeleteWorkspace(self._data.name())
        if data is not None:
            self._data = mantid.CloneWorkspace(InputWorkspace=data, OutputWorkspace='MantidWorkspaceCheckpoint-{}-data'.format(id(self)))

    def _clear_data(self):
        if self._data is not None:
            mantid.DeleteWorkspace(self._data.name())
            self._data = None

    def _initialize_from(self, data):
        self._data = mantid.CloneWorkspace(InputWorkspace=data, OutputWorkspace='MantidWorkspaceCheckpoint-{}-data'.format(id(self)))
