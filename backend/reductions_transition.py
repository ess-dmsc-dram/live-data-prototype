from mantid_workspace_transition import MantidWorkspaceTransition


class ReductionTransition(MantidWorkspaceTransition):
    def __init__(self, parent, reducer):
        self._reducer = reducer
        super(ReductionTransition, self).__init__(parents=[parent])

    def _do_transition(self, data):
        ws = data[0].data
        return self._reducer.reduce(ws, 'tmp')
