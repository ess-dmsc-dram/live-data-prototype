class Checkpoint(object):
    def __iter__(self):
        yield self

    def replace(self, data):
        raise RuntimeError('Checkpoint.replace() must be implemented in child classes!')

    def append(self, data):
        raise RuntimeError('Checkpoint.append() must be implemented in child classes!')


class DataCheckpoint(Checkpoint):
    def __init__(self):
        self._data = None

    def __nonzero__(self):
        return self._data is not None

    @property
    def data(self):
        return self._data

    def clear(self):
        self._clear_data()

    def replace(self, data):
        self._set_data(data)

    def append(self, data):
        if self._data is None:
            self._initialize_from(data)
        else:
            self._append_data(data)

    def _set_data(self, data):
        self._data = data

    def _clear_data(self):
        self._data = None

    def _append_data(self, data):
        self._data += data

    def _initialize_from(self, data):
        self.replace(data)


class CompositeCheckpoint(Checkpoint):
    def __init__(self, checkpoint_type=DataCheckpoint, leaf_count=0):
        self._leaves = []
        for i in range(leaf_count):
            self._leaves.append(checkpoint_type())

    def __iter__(self):
        for leaf in self._leaves:
            yield leaf

    def __len__(self):
        return len(self._leaves)

    def __getitem__(self, index):
        return self._leaves[index]

    def __getslice__(self, i, j):
        return self._leaves[i:j]

    # TODO should this be supported?
    def __setitem__(self, index, value):
        self._leaves[index] = value

    def __delitem__(self, index):
        del self._leaves[index]

    def __delslice__(self, i, j):
        del self._leaves[i:j]

    @property
    def data(self):
        return [ leaf.data for leaf in self._leaves ]

    def add_checkpoint(self, checkpoint):
        self._leaves.append(checkpoint)

    def remove_checkpoint(self, index):
        del self[index]

    def clear(self):
        for leaf in self._leaves:
            leaf.clear()

    def replace(self, data):
        # data should be iterable of same length as leaf
        for leaf, leaf_data in zip(self._leaves, data):
            leaf.replace(leaf_data)

    def append(self, data):
        # data should be iterable of same length as leaf
        for leaf, leaf_data in zip(self._leaves, data):
            leaf.append(leaf_data)


def coiterate(mastertree, slavetrees):
    if isinstance(mastertree, CompositeCheckpoint):
        for i, masterchild in enumerate(mastertree):
            slavechildren = tuple( s[i] for s in slavetrees )
            for item in coiterate(masterchild, slavechildren):
                yield item
    else:
        yield (mastertree,) + slavetrees
