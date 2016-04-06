import numpy
from mpi4py import MPI
import random
from transition import Transition
from histogram_checkpoint import HistogramCheckpoint


class GatherSpectraTransition(Transition):
    def __init__(self, parent):
        self._comm = MPI.COMM_WORLD
	self._spectra_id = '11'
        super(GatherSpectraTransition, self).__init__(parents=[parent])

    def _do_transition(self, data):
	index = int(self._spectra_id)
        data = data[0].data
        x = data.readX(index)
        y = data.readY(index)
        #gathered = self._comm.gather(bin_values, root=0)
        #if self._comm.Get_rank() == 0:
        #    bin_values = sum(gathered)
        return x, y, index

    def set_spectra_id(self, spectra_id):
        self._spectra_id = spectra_id
        self.trigger_rerun()

    def _create_checkpoint(self):
        return HistogramCheckpoint()
