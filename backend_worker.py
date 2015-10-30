from collections import deque
import zmq
import time
from mpi4py import MPI

from backend_heartbeat import BackendHeartbeat


class BackendWorker(object):
    def __init__(self, command_queue, communicator=MPI.COMM_WORLD, root_rank=0):
        self._comm = communicator
        self._rank = self._comm.Get_rank()
        self._root = root_rank
        self._heartbeat = BackendHeartbeat(self._comm, self._root)
        self._command_queue = command_queue
        self._last_processed_packet_index = 0

    def run(self):
        self._startup()
        while True:
            if self._is_root():
                if self._command_queue:
                    # beat says: process command
                    what, payload = self._heartbeat.put_user_command(self._command_queue.get()['payload']['bin_parameters'])
                elif self._can_process_data():
                    # beat says: process data
                    what, payload = self._heartbeat.put_control('process data')
                else:
                    # empty beat
                    what, payload = self._heartbeat.put_idle()
            else:
                what, payload = self._heartbeat.get()

            if what == 1:
                self._try_process_data()
            elif what == 2:
                print('{} got command'.format(time.time()))
                self._process_command(payload)
            else:
                # no data, no command, sleep till next beat
                time.sleep(0.05)

    def _startup(self):
        pass

    def _process_command(self, command):
        print('Rank {} {}: {} (processing not implemented)'.format(MPI.COMM_WORLD.Get_rank(), time.time(), command))

    def _try_process_data(self):
        while not self._process_data():
            time.sleep(0.05)

    def _is_root(self):
        return self._rank == self._root


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
        self._socket = context.socket(zmq.PULL)
        uri = 'tcp://{0}:{1:d}'.format(host, port)
        self._socket.connect(uri)
        print('Connected to command publisher at ' + uri)


class BackendCommandPublisher(object):
    def __init__(self, num_clients, host='*', port=10000):
        self._connect(host, port)
        self._num_clients = num_clients

    def publish(self, command):
        for i in range(self._num_clients):
            self._socket.send_json(command)

    def _connect(self, host, port):
        context = zmq.Context()
        self._socket = context.socket(zmq.PUSH)
        uri = 'tcp://{0}:{1:d}'.format(host, port)
        self._socket.bind(uri)
        print('BackendCommandPublisher: Bound to ' + uri)

