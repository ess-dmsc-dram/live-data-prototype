import numpy
from mpi4py import MPI
import random
from transition import Transition
from histogram_checkpoint import HistogramCheckpoint
import MPIDataSplit

class GatherSpectraTransition(Transition):
    def __init__(self, parent):
        self._comm = MPI.COMM_WORLD
	self._spectra_id = '1' #also set as 1 in backendreducer
        super(GatherSpectraTransition, self).__init__(parents=[parent])

    def _do_transition(self, data):
	index = int(self._spectra_id) #workspaceIndex
	target = MPIDataSplit.determine_data_split(index, self._comm.size)
        data = data[0].data
	x = data.readX(index)
	y = data.readY(index)
	if self._comm.Get_rank() == target:
		packet = numpy.concatenate((x, y))
  	    	requestXY = self._comm.isend(packet, dest=0) 
		requestXY.Wait()
        if self._comm.Get_rank() == 0:
	    	packet = self._comm.recv(source=target)
		x,y = numpy.array_split(packet, 2)
        return x, y, index



    def set_spectra_id(self, spectra_id):
        self._spectra_id = spectra_id
        self.trigger_rerun()

    def _create_checkpoint(self):
        return HistogramCheckpoint()
