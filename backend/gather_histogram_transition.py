import numpy
from mpi4py import MPI

from transition import Transition
from histogram_checkpoint import HistogramCheckpoint


class GatherHistogramTransition(Transition):
    def __init__(self, parent):
        self._comm = MPI.COMM_WORLD
        super(GatherHistogramTransition, self).__init__([parent])

    def _do_transition(self, data):
        if data is None:
            return data
        bin_boundaries = data.readX(0)
        bin_values = data.readY(0)
        gathered = self._comm.gather(bin_values, root=0)
        if self._comm.Get_rank() == 0:
            bin_values = sum(gathered)
        return bin_boundaries, bin_values

    def _get_output_checkpoint_type(self, input_checkpoint):
        # Output type is always HistogramCheckpoint, input_checkpoint ignored.
        return HistogramCheckpoint
