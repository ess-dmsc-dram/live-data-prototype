import time
import numpy
import zmq
from mpi4py import MPI

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
        print 'Starting EventListener...'
        self._connect()

    def _can_process_data(self):
        # TODO: for now we always say yes, i.e., we constantly wait for the stream
        return True

    def _process_data(self):
        # TODO: With this implementation the EventListener will not
        # react to commands unless stream data keeps coming in.
        data = self._receive_packet()
        split_data = self._distribute_stream(data)
        self._data_queue_out.put(split_data)
        return True

    def _connect(self):
        if self._comm.Get_rank() == 0:
            context = zmq.Context()
            self.socket = context.socket(zmq.PULL)
            uri = 'tcp://{0}:{1:d}'.format(self._host, self._port)
            self.socket.connect(uri)
            print 'Connected to event streamer at ' + uri

    def _receive_packet(self):
        if self._comm.Get_rank() == 0:
            header = self.socket.recv_json()
            payload = self.socket.recv()
            if header['type'] is 'meta_data':
                print('received meta data {}, dropping it.'.format(payload))
                return None
            record_type = header['record_type']
            return numpy.frombuffer(payload, dtype=record_type)
        else:
            return None

    def _distribute_stream(self, data):
        if self._comm.Get_rank() == 0:
            split = []
            for i in range(self._comm.size):
                split.append([])
            if data is not None:
                for i in data:
                    detector_id = int(i[0])
                    target = detector_id % self._comm.size
                    split[target].append(i)
        else:
            split = None
        return numpy.array(self._comm.scatter(split, root=0))
