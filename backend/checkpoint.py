class Checkpoint(object):
    def get_data(self):
        raise RuntimeError('Checkpoint.get_data() must be implemented in child classes!')

    def add_transition(self, transition):
        raise RuntimeError('Checkpoint.add_transition() must be implemented in child classes!')

    def replace(self, data):
        raise RuntimeError('Checkpoint.replace() must be implemented in child classes!')

    def append(self, data):
        raise RuntimeError('Checkpoint.append() must be implemented in child classes!')


class DataCheckpoint(Checkpoint):
    def __init__(self):
        self._data = None
        self._data_diff = None
        self._transitions = []

    def get_data(self):
        diff = self._data_diff
        # this class gives up ownership of the diff
        self._data_diff = None
        return self._data, diff

    def add_transition(self, transition):
        self._transitions.append(transition)
        transition.trigger_rerun()

    def replace(self, data):
        self._replace(data)
        self._trigger_transitions()

    def append(self, data):
        self._append(data)
        self._trigger_transitions()

    def _replace(self, data):
        self._data_diff = None
        self._data = data

    def _append(self, data):
        # keep the diff to allow transitions to work only based on that
        if self._transitions:
            self._data_diff = data
        if self._data is None:
            self._data = data
        else:
            self._data += data
            # ADS, your friendly helper...
            #DeleteWorkspace(data)

    def _trigger_transitions(self):
        for t in self._transitions:
            t.trigger_update()


class CompositeCheckpoint(Checkpoint):
    def __init__(self, leaf_count=0):
        self._leafs = []
        for i in range(leaf_count):
            self._leafs.append(DataCheckpoint())

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

    def add_transition(self, transition):
        for leaf in self._leafs:
            leaf.add_transition(transition)

    def replace(self, data):
        # data should be iterable of same length as leaf
        for leaf, leaf_data in zip(self._leafs, data):
            leaf.replace(leaf_data)

    def append(self, data):
        # data should be iterable of same length as leaf
        for leaf, leaf_data in zip(self._leafs, data):
            leaf.append(leaf_data)


