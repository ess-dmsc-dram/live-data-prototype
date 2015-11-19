class Checkpoint(object):
    def get_data(self):
        raise RuntimeError('Checkpoint.get_data() must be implemented in child classes!')

    def replace(self, data):
        raise RuntimeError('Checkpoint.replace() must be implemented in child classes!')

    def append(self, data):
        raise RuntimeError('Checkpoint.append() must be implemented in child classes!')


class DataCheckpoint(Checkpoint):
    def __init__(self):
        self._data = None
        self._data_diff = None

    @property
    def data(self):
        return self._data

    def get_data(self):
        return self._data, self._data_diff

    def clear(self):
        self._clear_data()
        self._clear_data_diff()

    def replace(self, data):
        self._clear_data_diff()
        self._set_data(data)

    def append(self, data):
        if self._data is None:
            self.replace(data)
        else:
            self._append_data(data)
            # Careful: _set_data_diff may invalidate data, so we call this last.
            self._set_data_diff(data)

    def _set_data_diff(self, data):
        self._data_diff = data

    def _clear_data_diff(self):
        self._data_diff = None

    def _set_data(self, data):
        self._data = data

    def _clear_data(self):
        self._data = None

    def _append_data(self, data):
        self._data += data


class CompositeCheckpoint(Checkpoint):
    def __init__(self, checkpoint_type=DataCheckpoint, leaf_count=0):
        self._leafs = []
        for i in range(leaf_count):
            self._leafs.append(checkpoint_type())

    def __len__(self):
        return len(self._leafs)

    def __getitem__(self, index):
        return self._leafs[index]

    def __getslice__(self, i, j):
        return self._leafs[i:j]

    # TODO should this be supported?
    def __setitem__(self, index, value):
        self._leafs[index] = value

    def __delitem__(self, index):
        del self._leafs[index]

    def __delslice__(self, i, j):
        del self._leafs[i:j]

    def add_checkpoint(self, checkpoint):
        self._leafs.append(checkpoint)

    def remove_checkpoint(self, index):
        del self[index]

    def get_data(self):
        return [ leaf.get_data() for leaf in self._leafs ]

    def clear(self):
        for leaf in self._leafs:
            leaf.clear()

    def replace(self, data):
        # data should be iterable of same length as leaf
        for leaf, leaf_data in zip(self._leafs, data):
            leaf.replace(leaf_data)

    def append(self, data):
        # data should be iterable of same length as leaf
        for leaf, leaf_data in zip(self._leafs, data):
            leaf.append(leaf_data)
