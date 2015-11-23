import mantid.simpleapi as mantid

from checkpoint import DataCheckpoint
from checkpoint import CompositeCheckpoint
from checkpoint import coiterate
from mantid_workspace_checkpoint import MantidWorkspaceCheckpoint
from transition import Transition


class MantidWorkspaceTransition(Transition):
    def __init__(self, create_checkpoint = lambda: DataCheckpoint(), parents = []):
        super(MantidWorkspaceTransition, self).__init__(create_checkpoint, parents)

    def trigger_update(self, update):
        result = Transition.trigger_update(self, update)
        # Remove temporary workspace from ADS
        # TODO Temporarily disabled
        #for base, diff in coiterate(self._checkpoint, (result,)):
        #    if isinstance(base, MantidWorkspaceCheckpoint) and diff:
        #        if base.data.name() != diff.data.name():
        #            print('WARNING: deleting {}'.format(diff.data.name()))
        #            mantid.DeleteWorkspace(diff.data.name())
