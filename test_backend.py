from backend_worker import BackendCommandQueue
from backend_mantid_reducer import BackendMantidReducer
from backend_mantid_reducer import BackendMantidRebinner
from backend import ResultPublisher
from zmq_queue import ZMQQueueServer
from zmq_queue import ZMQQueueClient
from parameter_control_server import ParameterControlServer
import ports

import threading
import time
import numpy
from mpi4py import MPI


rank = MPI.COMM_WORLD.Get_rank()
event_queue_port = 11000 + rank

event_queue_in = ZMQQueueClient(port=event_queue_port)
event_queue_in_thread = threading.Thread(target=event_queue_in.run)
event_queue_in_thread.start()

rebinner = BackendMantidRebinner()

if MPI.COMM_WORLD.Get_rank() == 0:
    command_queue = BackendCommandQueue(port=ports.rebin_control)
    command_queue_thread = threading.Thread(target=command_queue.run)
    command_queue_thread.start()
else:
    command_queue = None

reducer = BackendMantidReducer(command_queue, event_queue_in, rebinner)
reducer_thread = threading.Thread(target=reducer.run)
reducer_thread.start()

if MPI.COMM_WORLD.Get_rank() == 0:
    resultPublisher = ResultPublisher(rebinner)
    resultPublisher.start()
    parameterController = ParameterControlServer(port=ports.result_publisher_control, parameter_dict=resultPublisher.get_parameter_dict())
    parameterController_thread = threading.Thread(target=parameterController.run)
    parameterController_thread.start()

while threading.active_count() > 0:
    time.sleep(0.1)
