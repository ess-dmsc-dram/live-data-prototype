from collections import deque
import zmq
import time


# TODO: use IPC with a pipe instead of TCP

# Basically these two classes connect two deques via ZMQ:
# deque -> ZMQ -> deque
# threads working on boths deques continously move data from the deque on the server to the deque on the client


class ZMQQueueServer(object):
    def __init__(self, host='*', port=10000):
        self._host = host
        self._port = port
        self._deque = deque()

    def __len__(self):
        return len(self._deque)

    def run(self):
        print('Starting ZMQQueueServer')
        self._connect(self._host, self._port)
        while True:
            # wait for data
            # TODO proper sleep time
            while not self._deque:
                time.sleep(0.1)
            self._socket.send(self._deque.popleft())
            #print('Server, remaining length: {}'.format(len(self._deque)))

    def put(self, item):
        self._deque.append(item)

    def _connect(self, host, port):
        context = zmq.Context()
        self._socket = context.socket(zmq.PUSH)
        uri = 'tcp://{0}:{1:d}'.format(host, port)
        self._socket.bind(uri)
        print('ZMQQueueServer: Bound to ' + uri)


class ZMQQueueClient(object):
    def __init__(self, host='localhost', port=10000):
        self._host = host
        self._port = port
        self._deque = deque()
        self._connect(self._host, self._port)

    def __len__(self):
        return len(self._deque)

    def run(self):
        print('Starting ZMQQueueClient')
        while True:
            self._deque.append(self._socket.recv())

    def get(self):
        while not self._deque:
            time.sleep(0.1)
        #print('Client, remaining length: {}'.format(len(self._deque)-1))
        return self._deque.popleft()

    def _connect(self, host, port):
        context = zmq.Context()
        self._socket = context.socket(zmq.PULL)
        uri = 'tcp://{0}:{1:d}'.format(host, port)
        self._socket.connect(uri)
        print('ZMQQueueClient: Connected to ZMQQueueServer at ' + uri)
