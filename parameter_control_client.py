import zmq


class ParameterControlClient(object):
    def __init__(self, server, port, protocol_version=1):
        self._zmq_socket = self._init_zmq_socket(server, port)
        self._protocol_version = protocol_version

    def send(self, request_type, payload):
        self._zmq_socket.send_json(
            {'version': self._protocol_version,
             'request_type': request_type,
             'payload': payload}
        )

        server_reply = self._zmq_socket.recv_json()

        self._check_server_reply_version(server_reply)

        return server_reply

    def _check_server_reply_version(self, server_reply):
        if server_reply['version'] != self._protocol_version:
            raise RuntimeError('Server replied with unsupported version: {0}. Expected {1} instead.'.format(
                server_reply['version'], self._protocol_version))

    def _init_zmq_socket(sef, server, port):
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        socket.connect('tcp://{0}:{1}'.format(server, port))

        return socket

