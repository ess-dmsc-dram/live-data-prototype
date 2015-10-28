from threading import Thread
from collections import deque
import zmq


# TODO: use IPC with a pipe instead of TCP


class ZMQQueueServer(Thread):
    def __init__(self, host='*', port=10000):
        Thread.__init__(self)
        self._host = host
        self._port = port
        self._deque = deque()

    def __len__(self):
        return len(self._deque)

    def run(self):
        print('Starting ZMQQueueServer')
        self._connect(self._host, self._port)
        while True:
            command = self._socket.recv()
            if command == 'len':
                self._socket.send_json(len(self))
            elif command == 'get':
                self._socket.send(self._deque.popleft())
            else:
                self._socket.send('Unknown command')

    def put(self, item):
        self._deque.append(item)

    def _connect(self, host, port):
        context = zmq.Context()
        self._socket = context.socket(zmq.REP)
        uri = 'tcp://{0}:{1:d}'.format(host, port)
        self._socket.bind(uri)
        print('ZMQQueueServer: Bound to ' + uri)


class ZMQQueueClient(object):
    def __init__(self, host='localhost', port=10000):
        self._connect(host, port)

    def __len__(self):
        self._socket.send('len')
        return self._socket.recv_json()

    def get(self):
        self._socket.send('get')
        return self._socket.recv()

    def _connect(self, host, port):
        context = zmq.Context()
        self._socket = context.socket(zmq.REQ)
        uri = 'tcp://{0}:{1:d}'.format(host, port)
        self._socket.connect(uri)
        print('ZMQQueueClient: Connected to ZMQQueueServer at ' + uri)
