from backend_worker import BackendCommandQueue
from backend_event_listener import EventListener
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

event_queue_out = ZMQQueueServer(port=event_queue_port)
event_queue_out_thread = threading.Thread(target=event_queue_out.run)
event_queue_out_thread.start()

listener = EventListener(None, event_queue_out)
listener_thread = threading.Thread(target=listener.run)
listener_thread.start()
