import mantid.simpleapi as mantid

from checkpoint import DataCheckpoint


class MantidWorkspaceCheckpoint(DataCheckpoint):
    def __init__(self):
        super(MantidWorkspaceCheckpoint, self).__init__()

    def _set_data_diff(self, data):
        if self._data_diff is not None:
            mantid.DeleteWorkspace(self._data_diff.name())
        self._data_diff = mantid.RenameWorkspace(InputWorkspace=data, OutputWorkspace='MantidWorkspaceCheckpoint-{}-data_diff'.format(id(self)))

    def _clear_data_diff(self):
        if self._data_diff is not None:
            mantid.DeleteWorkspace(self._data_diff.name())
            self._data_diff = None

    def _set_data(self, data):
        if self._data is not None:
            mantid.DeleteWorkspace(self._data.name())
        if data is not None:
            self._data = mantid.RenameWorkspace(InputWorkspace=data, OutputWorkspace='MantidWorkspaceCheckpoint-{}-data'.format(id(self)))

    def _clear_data(self):
        if self._data is not None:
            mantid.DeleteWorkspace(self._data.name())
            self._data = None
