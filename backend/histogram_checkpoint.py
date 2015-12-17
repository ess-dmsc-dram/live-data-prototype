from copy import deepcopy

from checkpoint import DataCheckpoint


class HistogramCheckpoint(DataCheckpoint):
    def __init__(self):
        super(HistogramCheckpoint, self).__init__()

    @property
    def data(self):
        #TODO We return a deepcopy since this is used in another thread. However, this should be done somewhere else. This is not the place for it.
        return deepcopy(self._data)

    def _set_data(self, data):
        self._data = (deepcopy(data[0]), deepcopy(data[1]))

    def _append_data(self, data):
        self._data = (deepcopy(data[0]), self._data[1] + data[1])
