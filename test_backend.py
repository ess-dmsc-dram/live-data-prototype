from backend_event_listener import EventListener
from backend_mantid_reducer import BackendMantidReducer
from backend_mantid_reducer import BackendMantidRebinner
from backend import ResultPublisher
from zmq_queue import ZMQQueueServer
from zmq_queue import ZMQQueueClient
import threading
import time
import numpy
from mpi4py import MPI


rank = MPI.COMM_WORLD.Get_rank()
event_queue_port = 11000 + rank
reduced_event_queue_port = 12000 + rank

event_queue_out = ZMQQueueServer(port=event_queue_port)
event_queue_out_thread = threading.Thread(target=event_queue_out.run)
event_queue_out_thread.start()

listener = EventListener(None, event_queue_out)
listener_thread = threading.Thread(target=listener.run)
listener_thread.start()

event_queue_in = ZMQQueueClient(port=event_queue_port)
event_queue_in_thread = threading.Thread(target=event_queue_in.run)
event_queue_in_thread.start()

rebinner = BackendMantidRebinner()

#reduced_event_queue_out = ZMQQueueServer(port=reduced_event_queue_port)
#reduced_event_queue_out_thread = threading.Thread(target=reduced_event_queue_out.run)
#reduced_event_queue_out_thread.start()

reducer = BackendMantidReducer(None, event_queue_in, rebinner)
reducer_thread = threading.Thread(target=reducer.run)
reducer_thread.start()

if MPI.COMM_WORLD.Get_rank() == 0:
    resultPublisher = ResultPublisher(rebinner)
    resultPublisher.start()

while threading.active_count() > 0:
    time.sleep(0.1)

