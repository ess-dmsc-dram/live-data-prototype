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
	#if self._comm.Get_rank() == 0: #assuming rootrank
	#    self._comm.recv(index, source=MPI.ANY_SOURCE) #wants to receive the x,y data (and index?)
	#else:
	#    self._comm.send(index, dest=0) #if it is the rank with the readX/Y data, it wants to send it to the root rank
        return x, y, index

    def set_spectra_id(self, spectra_id):
        self._spectra_id = spectra_id
        self.trigger_rerun()

    def _create_checkpoint(self):
        return HistogramCheckpoint()
