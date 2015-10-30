import threading
import time
import numpy
import zmq
from mpi4py import MPI

import ports
import command_line_parser
from backend_worker import BackendWorker


# master connectes to main event stream and distributes it to all
# packets are put in a queue
class EventListener(BackendWorker):
    def __init__(self, command_queue, data_queue_out):
        BackendWorker.__init__(self, command_queue)
        self._data_queue_out = data_queue_out
        self._comm = MPI.COMM_WORLD
        self.socket = None

    def _startup(self):
        print 'Starting EventListener...'
        self._connect()
        self._get_stream_info()

    def _can_process_data(self):
        # TODO: for now we always say yes, i.e., we constantly wait for the stream
        return True

    def _process_data(self):
        # TODO: With this implementation the EventListener will not
        # react to commands unless stream data keeps coming in.
        data = self._get_data_from_stream()
        #print data
        split_data = self._distribute_stream(data)
        #print self._last_processed_packet_index, split_data
        self._data_queue_out.put(split_data)
        self._last_processed_packet_index += 1
        return True

    def _connect(self):
        if self._comm.Get_rank() == 0:
            context = zmq.Context()
            self.socket = context.socket(zmq.REQ)
            uri = 'tcp://{0}:{1:d}'.format(command_line_parser.get_host(), ports.event_stream)
            self.socket.connect(uri)
            print 'Connected to event streamer at ' + uri

    def _get_stream_info(self):
        if self._comm.Get_rank() == 0:
            self.socket.send('h')
            info = self.socket.recv_json()
            self.record_type = info['record_type']

    def _get_data_from_stream(self):
        if self._comm.Get_rank() == 0:
            self.socket.send('d')
            header = self.socket.recv_json()
            event_count = header['event_count']
            data = self.socket.recv()
            return numpy.frombuffer(data, dtype=self.record_type)
        else:
            return None

    def _distribute_stream(self, data):
        if self._comm.Get_rank() == 0:
            split = []
            for i in range(self._comm.size):
                split.append([])
            for i in data:
                detector_id = int(i[0])
                target = detector_id % self._comm.size
                split[target].append(i)
        else:
            split = None
        return numpy.array(self._comm.scatter(split, root=0))
