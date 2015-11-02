from backend_mantid_reducer import BackendMantidReducer
from backend_mantid_reducer import BackendMantidRebinner
from result_publisher import ResultPublisher
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

reducer = BackendMantidReducer(event_queue_in, rebinner)
reducer_thread = threading.Thread(target=reducer.run)
reducer_thread.start()

if MPI.COMM_WORLD.Get_rank() == 0:
    reducer_controller = ParameterControlServer(controllee=reducer, port=ports.rebin_control)
    reducer_controller_thread = threading.Thread(target=reducer_controller.run)
    reducer_controller_thread.start()

    resultPublisher = ResultPublisher(rebinner)
    resultPublisher_thread = threading.Thread(target=resultPublisher.run)
    resultPublisher_thread.start()

    parameterController = ParameterControlServer(controllee=resultPublisher, port=ports.result_publisher_control)
    parameterController_thread = threading.Thread(target=parameterController.run)
    parameterController_thread.start()

while threading.active_count() > 0:
    time.sleep(0.1)
