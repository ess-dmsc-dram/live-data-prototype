from collections import deque
import zmq
import time
from mpi4py import MPI


class BackendWorker(object):
    def __init__(self, command_queue):
        self._command_queue = command_queue
        self._last_processed_packet_index = 0

    def run(self):
        self._startup()
        while True:
            if self._command_queue:
                print('{} got command'.format(time.time()))
                indices = MPI.COMM_WORLD.allgather(self._last_processed_packet_index)
                print indices
                command_index = max(indices)
                print('{} command index will be {}'.format(time.time(), command_index))
                while command_index > self._last_processed_packet_index:
                    self._try_process_data()
                print('{} processing command'.format(time.time()))
                self._process_command(self._command_queue.get())
            else:
                self._try_process_data()

    def _startup(self):
        pass

    def _process_command(self, command):
        print('Rank {} {}: {} (processing not implemented)'.format(MPI.COMM_WORLD.Get_rank(), time.time(), command))

    def _try_process_data(self):
        if not self._process_data():
            time.sleep(0.05)
        #else:
        #    print('Process packet {}'.format(self._last_processed_packet_index))


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
            self._command_queue.append(self._socket.recv_json())

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
        self._socket.send_json(command)

    def _connect(self, host, port):
        context = zmq.Context()
        self._socket = context.socket(zmq.PUB)
        uri = 'tcp://{0}:{1:d}'.format(host, port)
        self._socket.bind(uri)
        print('BackendCommandPublisher: Bound to ' + uri)

