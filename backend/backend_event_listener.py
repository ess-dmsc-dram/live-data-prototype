import time
import numpy
import zmq
from mpi4py import MPI

from logger import log
from backend_worker import BackendWorker


# master connectes to main event stream and distributes it to all
# packets are put in a queue
class BackendEventListener(BackendWorker):
    def __init__(self, data_queue_out, host, port):
        BackendWorker.__init__(self)
        self._data_queue_out = data_queue_out
        self.socket = None
        self._host = host
        self._port = port

    def _startup(self):
        log.info('Starting EventListener...')
        self._connect()

    def _can_process_data(self):
        # TODO: for now we always say yes, i.e., we constantly wait for the stream
        return True

    def _process_data(self):
        # TODO: With this implementation the EventListener will not
        # react to commands unless stream data keeps coming in.
        what, data = self._receive_packet()
        split_data = self._distribute_stream(what, data)
        self._data_queue_out.put(split_data)
        return True

    def _connect(self):
        if self._comm.Get_rank() == 0:
            context = zmq.Context()
            self.socket = context.socket(zmq.PULL)
            uri = 'tcp://{0}:{1:d}'.format(self._host, self._port)
            self.socket.connect(uri)
            log.info('Connected to event streamer at {}'.format(uri))

    def _receive_packet(self):
        if self._comm.Get_rank() == 0:
            header = self.socket.recv_json()
            payload = self.socket.recv()
            if header['type'] == 'meta_data':
                return 'meta_data', payload
            record_type = header['record_type']
            return 'event_data', numpy.frombuffer(payload, dtype=record_type)
        else:
            return None, None

    def _distribute_stream(self, what, data):
        if self._comm.Get_rank() == 0:
            if what == 'meta_data':
                split = [data] * self._comm.size
            else:
		#split = distribute_stream_split(self._comm.size, data)
                split = []
                for i in range(self._comm.size):
                    split.append([])
                for i in data: #make this into a separate function to be used by here and spectra_transition    
                    detector_id = int(i[0]) 
		    #print "this is detector ID"
		    #print detector_id
                    target = detector_id % self._comm.size
		    #print "whatever i is:"
		    #print i
                    split[target].append(i)
        else:
            split = None
        what = self._comm.scatter([what]*self._comm.size, root=0)
        data = self._comm.scatter(split, root=0)
        if what == 'meta_data':
            return what, data
        else:
            return what, numpy.array(data)

#distribute_stream_split(comm_size, data):
#   split = []
#    for i in range(comm.size):
#   	split.append([])
#    for i in data: 
#     	detector_id = int(i[0])
#      	target = detector_id % comm.size
#      	split[target].append(i)

