import numpy
from mpi4py import MPI
import random
from transition import Transition
from histogram_checkpoint import HistogramCheckpoint


class GatherSpectraTransition(Transition):
    def __init__(self, parent):
        self._comm = MPI.COMM_WORLD
	self._spectra_id = '1' #also set as 1 in backendreducer
        super(GatherSpectraTransition, self).__init__(parents=[parent])

    def _do_transition(self, data):
	index = int(self._spectra_id) #workspaceIndex
	#print index
	#index = 11
	target = index % self._comm.size #target now mpi process with det id information
	#print target
        data = data[0].data
	x = data.readX(index)
	y = data.readY(index)
	if target is not 0: #to avoid the target being 0 and then requesting information for itself, which when using blocking sends and recieves would hang the program
	    if self._comm.Get_rank() == target:
		self._comm.send(x, dest = 0)
		self._comm.send(y, dest = 0)
	    if self._comm.Get_rank() == 0:
		x = self._comm.recv(source=target)
		y = self._comm.recv(source=target)	   
# if self._comm.Get_rank() == target: #assuming rootrank
#  	    	request = self._comm.Isend(x, dest=0) #as request object, use wait method on it later on, can lower case this for picking any python object
#	    	request = self._comm.Isend(y, dest=0)   
 #           if self._comm.Get_rank() == 0:
#	    	x = self._comm.recv(source=target)
#	    	y = self._comm.recv(source=target)
	

        return x, y, index
#assume has knowledge of index of data
#find out which rank has the data assoc with the index
#specifically query that rank to get the data 



    def set_spectra_id(self, spectra_id):
        self._spectra_id = spectra_id
        self.trigger_rerun()

    def _create_checkpoint(self):
        return HistogramCheckpoint()
