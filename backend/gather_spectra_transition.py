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
	#get knowledge of index required (not all processes know this?)
	index = int(self._spectra_id)
	print "my rank is"
	print self._comm.Get_rank()
	print "the index i know is"
	print index
        data = data[0].data
	x = data.readX(index)
	y = data.readY(index)
#	if self._comm.Get_rank() == 0: #assuming rootrank
#            self._comm.recv(x, source=MPI.ANY_SOURCE) #wants to receive the x,y data (and index?)
#        else:
#	    try:
#		print "got here!"
#	    	x = data.readX(index)
#	    	y = data.readY(index)
#	    	self._comm.send(x)
#	    except:
#	    	pass	
#        

        return x, y, index
#assume has knowledge of index of data
#find out which rank has the data assoc with the index
#specifically query that rank to get the data 



    def set_spectra_id(self, spectra_id):
        self._spectra_id = spectra_id
        self.trigger_rerun()

    def _create_checkpoint(self):
        return HistogramCheckpoint()
