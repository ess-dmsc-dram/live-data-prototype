import struct

from mpi4py import MPI


# Sends a small "heartbeat" that can contain commands.
#
# Small size for default heartbeat, 64 Byte should be small enough
# to be below the point where MPI broadcast slows down significantly.
#
# bytes | description | values
# 0     | type        | idle=0, control=1, user_cmd=2
# 1-10  | padding | -
# 12-15 | paylad length | uint32, giving size in Byte
# 16-63 | inline command payload

class BackendHeartbeat(object):
    def __init__(self, communicator=MPI.COMM_WORLD, root_rank=0):
        self._comm = communicator
        self._rank = self._comm.Get_rank()
        self._root = root_rank

    def get(self, command=None):
        header = bytearray(64)
        return self._broadcast_and_unpack(header)

    def put_idle(self):
        header = self._create_idle_header()
        return self._broadcast_and_unpack(header)

    def put_control(self, data):
        header = self._create_control_header(data)
        return self._broadcast_and_unpack(header)

    def put_user_command(self, command):
        header = self._create_user_command_header(command)
        return self._broadcast_and_unpack(header)

    def _broadcast_and_unpack(self, header):
        self._comm.Bcast([header, 64, MPI.BYTE], root=self._root)
        packet_type, payload_length, payload = self._unpack_header(header)
        if packet_type == 0:
            return 0, None
        # Note: mpi4py lower-case deals with things under the hood,
        # probably at the cost of speed, but long command should be rare.
        if payload_length > 48:
            return packet_type, self._comm.bcast(command)
        elif payload_length > 0:
            return packet_type, payload
        else:
            return packet_type, None

    def _create_idle_header(self):
        # 0 = idle
        return struct.pack('b63x', 0)

    def _create_data_header(self, data_type, data):
        # TODO this will break badly unless data has items of size byte
        return struct.pack('b11xI48s', data_type, len(data), str(data))

    def _create_control_header(self, data):
        # 1 = control
        return self._create_data_header(1, data)

    def _create_user_command_header(self, command):
        # 2 = user command
        return self._create_data_header(2, command)

    #def _create_header(self, command):
    #    if command == None:
    #        return struct.pack('11xbI48s', 0, 0, str())
    #    else:
    #        return struct.pack('11xbI48s', 1, len(command), str(command))

    def _unpack_header(self, header):
        data = struct.unpack('b11xI48s', header)
        packet_type = data[0]
        payload_length = data[1]
        payload = data[2][:payload_length]
        return packet_type, payload_length, payload
