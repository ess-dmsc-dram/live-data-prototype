import struct

from mpi4py import MPI


class BackendHeartbeat(object):
    def __init__(self, communicator=MPI.COMM_WORLD, root_rank=0):
        self._comm = communicator
        self._rank = self._comm.Get_rank()
        self._root = root_rank

    def beat(self, command=None):
        header = self._create_header(command)
        self._comm.Bcast([header, 64, MPI.BYTE], root=self._root)
        command_type, command_size, command_payload = self._unpack_header(header)
        # Note: mpi4py lower-case deals with things under the hood,
        # probably at the cost of speed, but long command should be rare.
        if command_size > 48:
            return self._comm.bcast(command)
        elif command_size > 0:
            return command_payload
        else:
            return None

    def _create_header(self, command):
        if self._rank != self._root:
            return bytearray(64)
        # small size for default heartbeat, 64 Byte should be small enough
        # to be below the point where MPI broadcast slows down significantly.
        #
        # bytes | description | values
        # 0-10  | padding | -
        # 11    | command type | 0=none, 1=attached, 2=separate
        # 12-15 | command length | uint32, giving size in Byte
        # 16-63 | inline command payload

        # TODO this will break badly unless command has items of size byte
        if command == None:
            return struct.pack('11xbI48s', 0, 0, str())
        else:
            return struct.pack('11xbI48s', 1, len(command), command)

    def _unpack_header(self, header):
        data = struct.unpack('11xbI48s', header)
        command_type = data[0]
        command_length = data[1]
        command_payload = data[2][:command_length]
        return command_type, command_length, command_payload
