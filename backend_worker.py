from collections import deque
import zmq
import time
from mpi4py import MPI


class BackendWorker(object):
    def __init__(self, command_queue, data_queue_in, data_queue_out):
        self._command_queue = command_queue
        self._data_queue_in = data_queue_in
        self._data_queue_out = data_queue_out

    def run(self):
        while True:
            if self._command_queue:
                command_index = max(MPI.COMM_WORLD.allgather(self._last_processed_packet_index))
                while command_index > self._last_processed_packet_index:
                    self._try_process_packet()
                self._process_command(self._command_queue.get())
            else:
                self._try_process_packet()

    def _process_command(self, command):
        print('Rank {} {}: {}'.format(MPI.COMM_WORLD.Get_rank(), time.time(), command))

    def _try_process_packet(self):
        if self._data_queue_in:
            data = self._data_queue_in.get()
            self._last_processed_packet_index = int(data)
            #self._process_packet(data)
            print('Rank {} {}: processed packet {}'.format(MPI.COMM_WORLD.Get_rank(), time.time(), self._last_processed_packet_index))
        else:
            time.sleep(0.05)


class BackendCommandQueue(object):
    def __init__(self, host='localhost', port=10000):
        self._host = host
        self._port = port
        self._command_queue = deque()

    def __len__(self):
        return len(self._command_queue)

    def get(self):
        return self._command_queue.popleft()

    def run(self):
        print 'Starting BackendCommandQueue...'
        self._connect(self._host, self._port)
        while True:
            self._command_queue.append(self._socket.recv())

    def _connect(self, host, port):
        context = zmq.Context()
        self._socket = context.socket(zmq.SUB)
        uri = 'tcp://{0}:{1:d}'.format(host, port)
        self._socket.connect(uri)
        self._socket.setsockopt(zmq.SUBSCRIBE, '')
        print('Substribed to command publisher at ' + uri)


class BackendCommandPublisher(object):
    def __init__(self, host='*', port=10000):
        self._connect(host, port)

    def publish(self, command):
        self._socket.send(command)

    def _connect(self, host, port):
        context = zmq.Context()
        self._socket = context.socket(zmq.PUB)
        uri = 'tcp://{0}:{1:d}'.format(host, port)
        self._socket.bind(uri)
        print('BackendCommandPublisher: Bound to ' + uri)

