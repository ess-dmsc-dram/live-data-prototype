from backend_worker import BackendCommandQueue
from backend_mantid_reducer import BackendMantidReducer
from backend_mantid_reducer import BackendMantidRebinner
from backend import ResultPublisher
from zmq_queue import ZMQQueueServer
from zmq_queue import ZMQQueueClient
from distributed_parameter_control_server import DistributedParameterControlServer
import ports

import threading
import time
import numpy
from mpi4py import MPI


rank = MPI.COMM_WORLD.Get_rank()
event_queue_port = 11000 + rank
reduced_event_queue_port = 12000 + rank

event_queue_in = ZMQQueueClient(port=event_queue_port)
event_queue_in_thread = threading.Thread(target=event_queue_in.run)
event_queue_in_thread.start()

rebinner = BackendMantidRebinner()

command_queue = BackendCommandQueue(port=ports.rebin_control)
command_queue_thread = threading.Thread(target=command_queue.run)
command_queue_thread.start()

reducer = BackendMantidReducer(command_queue, event_queue_in, rebinner)
reducer_thread = threading.Thread(target=reducer.run)
reducer_thread.start()

#binController = DistributedParameterControlServer(port=ports.rebin_control, parameter_dict=rebinner.get_parameter_dict())
#binController.start()

if MPI.COMM_WORLD.Get_rank() == 0:
    resultPublisher = ResultPublisher(rebinner)
    resultPublisher.set_update_rate(0.2)
    resultPublisher.start()

while threading.active_count() > 0:
    time.sleep(0.1)

