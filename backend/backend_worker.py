from collections import deque
import zmq
import time
from mpi4py import MPI

from logger import log
from backend_heartbeat import BackendHeartbeat
from controllable import Controllable


class BackendWorker(Controllable):
    def __init__(self, communicator=MPI.COMM_WORLD, root_rank=0):
        super(BackendWorker, self).__init__(type(self).__name__)
        self._comm = communicator
        self._rank = self._comm.Get_rank()
        self._root = root_rank
        self._heartbeat = BackendHeartbeat(self._comm, self._root)
        self._command_queue = deque()

    def process_instruction(self, instruction, argument):
        self._command_queue.append((instruction, argument))

    def run(self):
        self._startup()
        while True:
            what, payload = self._do_heartbeat()
            if what == 1:
                self._try_process_data()
            elif what == 2:
                log.debug('{} got command'.format(time.time()))
                self._process_command(payload)
            else:
                # no data, no command, sleep till next beat
                time.sleep(0.05)

    def _startup(self):
        pass

    def _do_heartbeat(self):
        if self._is_root():
            if self._command_queue:
                # beat says: process command
                return self._heartbeat.put_user_command(self._command_queue.popleft())
            elif self._can_process_data():
                # beat says: process data
                return self._heartbeat.put_control('process data')
            else:
                # empty beat
                return self._heartbeat.put_idle()
        else:
            return self._heartbeat.get()

    def _process_command(self, command):
        log.debug('Rank {} {}: {} (processing not implemented)'.format(MPI.COMM_WORLD.Get_rank(), time.time(), command))

    def _try_process_data(self):
        while not self._process_data():
            time.sleep(0.05)

    def _is_root(self):
        return self._rank == self._root
